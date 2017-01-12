#!/bin/bash

sqlite3 -line database.db 'update users set verified=1  where name="John Hammond";'
