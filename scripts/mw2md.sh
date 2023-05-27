#!/bin/bash

tr -d "{}"  | pandoc -f mediawiki -t markdown
