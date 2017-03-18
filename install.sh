#!/bin/bash

pyinstaller -F -y --clean main.py
cp post.pkl comment.pkl database.db ./dist/