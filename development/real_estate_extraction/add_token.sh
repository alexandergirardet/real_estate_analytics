#!/bin/bash

# Execute first command
command1="gcloud auth activate-service-account --key-file ./real-estate-dev-key.json"
$command1

# Execute second command
command2="gcloud auth print-access-token"
$command2

# Redirect the output of the final command to a file
output_file="access_token.txt"
$command2 > $output_file