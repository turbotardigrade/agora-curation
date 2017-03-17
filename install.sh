#!/bin/bash

pyinstaller --add-data "post.pkl:./" --add-data "comment.pkl:./" --add-data "database.db:./" -y main.py