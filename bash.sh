#!/bin/bash

# Run scrapper.py to get the CA
python3 scrapper.py AsimHay70862557

# Wait until the address is fetched and written to the file
while [ ! -s sol_address.txt ]; do
  sleep 1
done

# Read the CA from the file
CA=$(cat sol_address.txt)

# Run main.py with the CA as an argument
python3 main.py $CA
