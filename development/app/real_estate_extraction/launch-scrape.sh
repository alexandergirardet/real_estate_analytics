#!/bin/bash

# Execute first command
command1="./add_token.sh"
$command1

command2="python ./scrapy-test.py"
$command2

command3="./remove_token.sh"
$command3

command4="echo Token file removed"
$command4