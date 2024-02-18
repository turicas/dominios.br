#!/bin/bash

url="https://dumps.wikimedia.org/ptwiki/20240201/ptwiki-20240201-pages-articles-multistream.xml.bz2"
data_path="./data"
filename="$data_path/ptwiki.xml.bz2"
br_domains_filename="$data_path/domains-br-ptwiki.csv"
mkdir -p "$data_path"

# Download the compressed ptwiki XML
if [[ ! -e $filename ]]; then
  wget -c -t 0 -O "$filename" "$url"
else
  echo "File downloaded already"
fi

# extract links and then domains from these links
echo "ocorrencias,dominio" > "$br_domains_filename"
bzcat "$filename" \
	| grep -Eo --color=no 'https?://[^ ]+' \
	| sed -E 's#https?://##; s/\/.*$//' \
	| python tld_br.py filter \
	| sort | uniq -c | sort -nr \
	| sed -E 's/^ *//; s/ /,/' \
	>> "$br_domains_filename"
