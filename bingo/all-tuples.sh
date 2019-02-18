#!/usr/bin/env bash
sed 's/.*: //' | sed 's/NOT //g' | sed 's/, /\n/g' | sort | uniq
