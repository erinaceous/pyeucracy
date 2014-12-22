#!/bin/bash
socat tcp-listen:3057,fork SYSTEM:'echo HTTP/1.0 200; echo Content-Type\: text/plain; echo; ./get_contacts_tsv.sh'
