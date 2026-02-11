#!/bin/bash
echo "Checking backend logs for errors..."
doctl apps logs 2991840f-b2c1-4f2c-88fa-1ffd9f8401c9 cable-ticketing-backend --tail 100
