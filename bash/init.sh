#!/bin/bash
cd "$(dirname "$0")"
cp bashrc ~/.bashrc
echo "$1" >> ~/.bashrc
