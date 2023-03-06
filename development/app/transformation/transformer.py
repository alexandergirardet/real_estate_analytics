import pickle
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Handle the exception here
            print(f"This is a major ERROR and I will trigger the function that stores this data in another folder: {e}")
            # You can also raise a custom exception here if needed
    return wrapper

class ParquetTransformer:
    def __init__(self):
        self.expected_schema = self.load_schema()
        
        schema_columns = self.load_schema_columns()
        self.columns_to_keep = schema_columns['columns_to_keep']
        self.number_columns = schema_columns['number_columns']
        self.object_columns = schema_columns['object_columns']
        self.boolean_columns = schema_columns['boolean_columns']
        self.denormalize_list = schema_columns['denormalize_list']
        
    # Loading variables    
    def load_schema(self):
        with open('/Users/alexandergirardet/projects/estatewise/real_estate_analytics/development/notebooks/data_quality/parquet_schema.pkl', 'rb') as file:
            schema = pickle.loads(file.read())
        return schema
    
    def load_schema_columns(self):
        with open("/Users/alexandergirardet/projects/estatewise/real_estate_analytics/development/notebooks/data_quality/columns_schema.json", "r") as file:
            columns_schema = json.load(file)
        return columns_schema
    
    # JSON Functions
    def load_data(self, file_name):
        with open(f'data/{file_name}', 'r') as f:
            data = json.load(f)
        return data

    @handle_exceptions
    def normalize_data(self, property_data):
        normalized_data = pd.json_normalize(property_data)
        return normalized_data
    

    @handle_exceptions
    def drop_columns(self, normalized_df):
        normalized_df = normalized_df[self.columns_to_keep]
        return normalized_df

    @handle_exceptions
    def coerce_values(self, normalized_df):
        normalized_df['id'] = normalized_df['id'].astype(int)
        normalized_df[self.number_columns] = normalized_df[self.number_columns].astype(float)
        normalized_df[self.object_columns] = normalized_df[self.object_columns].astype(object)
        normalized_df[self.boolean_columns] = normalized_df[self.boolean_columns].astype(bool)

        return normalized_df
    
    # Handling functions
    @handle_exceptions
    def handle_embedded_data(self, transformed_df):
        transformed_df['feature_list'] = transformed_df['feature_list'].apply(self.handle_feature_list)
        transformed_df['propertyImages.images'] = transformed_df['propertyImages.images'].apply(self.handle_property_images)
        transformed_df['price.displayPrices'] = transformed_df['price.displayPrices'].apply(self.handle_display_prices)
        return transformed_df
    
    @handle_exceptions
    def handle_feature_list(self, feature_list):
        if feature_list is not None:
            if len(feature_list) > 0:
                feature_list = [str(x) for x in feature_list]
            else:
                feature_list = ['']
        else:
            feature_list = ['']
        return feature_list


    @handle_exceptions
    def handle_property_images(self, property_images):
        keys = ['srcUrl', 'url', 'caption']

        for property_image in property_images:
            for key, value in property_image.items():
                if key in keys:
                    try:
                        property_image[key] = str(value)
                    except:
                        property_image[key] = "null"

        return property_images 
    
    @handle_exceptions
    def handle_display_prices(self, display_prices):
        keys = ['displayPrice', 'displayPriceQualifier']

        for display_price in display_prices:
            for key, value in display_price.items():
                if key in keys:
                    try:
                        display_price[key] = str(value)
                    except:
                        display_price[key] = "null"

        return display_prices 
    
    @handle_exceptions
    def handle_nulls(self, normalized_df):
        normalized_df[self.object_columns] = normalized_df[self.object_columns].fillna("")
        
        return normalized_df
    
    # Denormalizing functions
    @handle_exceptions
    def denormalize_property(self, data_point, denormalize_list):
        denormalized_dict = {}
        for key, value in data_point.items():
            if '.' in key:
                base_column = key.split('.')[0]
                embedded_column = key.split('.')[1]
                if base_column in denormalized_dict.keys():
                    denormalized_dict[base_column][str(embedded_column)] = value
                else:
                    denormalized_dict[base_column] = {}
                    denormalized_dict[base_column][str(embedded_column)] = value
            else:
                denormalized_dict[key] = value
            
        return denormalized_dict
     
    @handle_exceptions
    def denormalize_properties(self, processed_data):
        processed_properties = processed_data.to_dict(orient="records")
        full_processed_properties = []
        for process_property in processed_properties:
            denormalized_processed_data = self.denormalize_property(process_property, self.denormalize_list)
            full_processed_properties.append(denormalized_processed_data)
                               
        return full_processed_properties
                               
    # Validate parquet        
    @handle_exceptions
    def validate_parquet(self, data):
        """
        Converts a list of dictionaries to a PyArrow table in Parquet format,
        retrieves its schema, and validates it against an expected schema.

        Args:
            data (list of dict): A list of dictionaries representing the data.
            expected_schema (pyarrow.Schema): The expected schema for the data.

        Returns:
            bool: True if the schema matches the expected schema, False otherwise.
        """

        # Convert data to PyArrow table
        table = pa.Table.from_pydict({k: [d[k] for d in data] for k in data[0]})

        # Write PyArrow table to Parquet file in memory
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink)
        buffer = sink.getvalue()

        # Read Parquet file back in from memory as PyArrow table
        table = pq.read_table(buffer)

        # Get schema of PyArrow table
        actual_schema = table.schema

        # Compare actual schema to expected schema
        schema_match = actual_schema.equals(self.expected_schema)

        # DataFrame convertion
        # dataframe = pd.DataFrame(data)
                               
        return schema_match
    
    def transform_data(self, data: list) -> list:
        """Takes a list of dictionaries and transforms, normalizes, and validates the data.

        Args:
            data (list): List of dictionaries representing the data.

        Returns:
            list: Two lists of dictionaries, one for valid data and one for invalid data.
        """
        validated_data = []
        invalid_data = []
        # invalid_data_index = []
        # data = self.load_data(file_name)
        normalized_df = self.normalize_data(data)
        normalized_df = self.drop_columns(normalized_df)
        normalized_df = self.handle_nulls(normalized_df)
        properties = normalized_df.to_dict(orient="records")
        for i, single_property in enumerate(properties):
            normalized_df = pd.DataFrame.from_dict([single_property])
            transformed_df = self.coerce_values(normalized_df)
            processed_df = self.handle_embedded_data(transformed_df)
            data = self.denormalize_properties(processed_df)
            validated = self.validate_parquet(data)
            
            if validated:
                validated_data += data
            else:
                invalid_data += data    
                # invalid_data_index.append(i)

                
        return validated_data, invalid_data