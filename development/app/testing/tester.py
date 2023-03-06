import random

class ValidationTester:

    def __init__(self, number_of_randoms):
        self.number_of_randoms = number_of_randoms

    def get_random_numbers(self):
        return random.sample(range(0, 50), self.number_of_randoms)

    def add_random_column(self, item):
        """
        Adds a random column to each dict in the given list of dicts.
        The column name is a random string of length 5, and the column
        value is a random integer between 1 and 100.
        """
        col_name = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=5))
        col_value = random.randint(1, 100)
        item[col_name] = col_value

        return col_name

    def remove_random_column(self, item):
        """
        Removes a random column from each dict in the given list of dicts.
        """
        if len(item) > 1:
            col_name = random.choice(list(item.keys()))
            del item[col_name]
            return col_name

    def change_random_value_type(self, item):
        """
        Changes the data type of a random value in each dict in the given list of dicts.
        The new data type is chosen randomly from float, int, and str.
        """
        col_name = random.choice(list(item.keys()))
        new_type = random.choice([float, int, str])
        if new_type == float:
            item[col_name] = 666
        elif new_type == int:
            item[col_name] = 666
        else:
            item[col_name] = "Test"

        return col_name

    def nullify_id(self, item):
        """
        Sets the value of the 'id' key to None in a random dict in the given list of dicts.
        """
        item['id'] = None
        
    def randomize_data(self, data):

        random_numbers = self.get_random_numbers()
        # random_functions = [self.add_random_column, self.remove_random_column, self.change_random_value_type, self.nullify_id]
        random_functions = [self.add_random_column, self.remove_random_column, self.change_random_value_type]
        for i, item in enumerate(data):
            if i in random_numbers:
                func = random.choice(random_functions)
                func_name = func.__name__
                column_name = func(item)
                print(f"Item {i}, is being randomized by the {func_name} function on the column: {column_name}")

        return data