#!/bin/bash
source .env

# If PUZZLE_USER_DOMAIN is empty, omit it from the mutation
if [ -z "$PUZZLE_USER_DOMAIN" ]; then
    cookie=$(curl --request POST \
    --silent --output /dev/null --cookie-jar - \
    --url "$PUZZLE_API" \
    --header 'Content-Type: application/json' \
    --data "{
    \"query\": \"mutation login{login(username: \\\"$PUZZLE_USERNAME\\\", password: \\\"$PUZZLE_PASSWORD\\\") {\n\t\tid\n\t\tnbf\n\t\texp\n\t}\n}\n\",
    \"operationName\": \"login\"
    }" | grep HttpOnly | awk '{print $7}')
else
    cookie=$(curl --request POST \
    --silent --output /dev/null --cookie-jar - \
    --url "$PUZZLE_API" \
    --header 'Content-Type: application/json' \
    --data "{
    \"query\": \"mutation login{login(domainName: \\\"$PUZZLE_USER_DOMAIN\\\", username: \\\"$PUZZLE_USERNAME\\\", password: \\\"$PUZZLE_PASSWORD\\\") {\n\t\tid\n\t\tnbf\n\t\texp\n\t}\n}\n\",
    \"operationName\": \"login\"
    }" | grep HttpOnly | awk '{print $7}')
fi
cynic introspect "$PUZZLE_API" -H "Cookie: id=$cookie"