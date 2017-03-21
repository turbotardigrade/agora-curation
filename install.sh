#!/bin/bash
cd curation
pyinstaller -F -y --clean main.py
cp post.pkl comment.pkl database.db ./dist/
cp -R dist ../