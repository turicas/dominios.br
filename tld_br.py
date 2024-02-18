import re
from functools import cached_property, lru_cache
from pathlib import Path
from textwrap import dedent

import requests
from lxml.html import document_fromstring


def br_tlds():
    response = requests.get("https://registro.br/dominio/categorias/")
    tree = document_fromstring(response.content)
    sections = tree.xpath("//div[@class = 'categories']//section")
    for section in sections:
        title = section.xpath(".//h2//text()")[0].strip()
        subtitle = section.xpath("./p[1]//text()")
        subtitle = subtitle[0].strip() if subtitle else None
        restriction = None
        for li in section.xpath(".//ul/li"):
            tld, description = li.xpath("./strong/text()"), li.xpath("./p/text()")
            if not description:
                restriction = tld[0]
                continue
            yield {
                "tld": tld[0],
                "title": title,
                "description": description[0],
                "target": subtitle,
                "restriction": restriction,
            }


def br_domain_tld_regexp(tlds):
    # XXX: using a regexp to extract the domain will only work because .br has only one and two levels (as in
    # `label.br` and `label.tld.br`)
    tld_pattern = "|".join(sorted(re.escape(item) for item in tlds))
    return dedent(
        r"""
            (?:[^a-z0-9àáâãéêíóôõúüç-]|^)+  # Equivalente a `\b` (boundary) porém inclui alguns caracteres acentuados
            ([a-z0-9àáâãéêíóôõúüç-]+\.)*    # Subdomínios opcionais
            (
                [a-z0-9àáâãéêíóôõúüç-]+\.
                (?:{tld_pattern})
            )                               # Label + TLD
            (?:[^a-z0-9àáâãéêíóôõúüç-]|$)+  # Equivalente a `\b` (boundary) porém inclui alguns caracteres acentuados
        """
    ).format(tld_pattern=tld_pattern)


class BRDomainMatcher:

    def __init__(self, input_csv: Path=None, encoding="utf-8"):
        if input_csv is None:
            self.tlds = set(row["tld"] for row in br_tlds())
        else:
            with input_csv.open(encoding=encoding) as fobj:
                self.tlds = set(row["tld"] for row in csv.DictReader(fobj))
        self.regexp = re.compile(
            br_domain_tld_regexp(list(self.tlds) + ["br"]),
            flags=re.VERBOSE | re.IGNORECASE | re.UNICODE,
        )

    def find(self, text):
        results = self.regexp.findall(text)
        answer = []
        for label, tld in results:
            if not label:
                if tld not in self.tlds:  # label.br
                    answer.append((tld, "br"))
                else:
                    answer.append((None, tld))
            elif tld in self.tlds:
                answer.append((label + tld, tld))
        return answer


class TestMatcher:

    @cached_property
    def matcher(self):
        return BRDomainMatcher()

    def test_happy_path_no_www(self):
        value = "mydomain.com.br"
        expected = [("mydomain.com.br", "com.br")]
        assert self.matcher.find(value) == expected

        value = "olar.edu.br"
        expected = [("olar.edu.br", "edu.br")]
        assert self.matcher.find(value) == expected

    def test_happy_path_www(self):
        value = "www.mydomain.com.br"
        expected = [("mydomain.com.br", "com.br")]
        assert self.matcher.find(value) == expected

        value = "www.olar.edu.br"
        expected = [("olar.edu.br", "edu.br")]
        assert self.matcher.find(value) == expected

    def test_happy_path_multiple_subdomains(self):
        value = "www.sub1.sub2.sub3.domain.com.br"
        expected = [("domain.com.br", "com.br")]
        assert self.matcher.find(value) == expected

    def test_happy_path_special_chars(self):
        value = "maçã.com.br álvaro.test.br"
        expected = [("maçã.com.br", "com.br"), ("test.br", "br")]
        assert self.matcher.find(value) == expected

        value = "olar.edu.br"
        expected = [("olar.edu.br", "edu.br")]
        assert self.matcher.find(value) == expected

    def test_happy_path_mixed_with_text(self):
        value = "Olá, como vai? Meu site é: https://www.mydomain.com.br/pagina/oi.html"
        expected = [("mydomain.com.br", "com.br")]
        assert self.matcher.find(value) == expected

        value = "Olá, como vai? Meu site é: http://olar.edu.br/pagina/oi.html"
        expected = [("olar.edu.br", "edu.br")]
        assert self.matcher.find(value) == expected

    def test_br_tld(self):
        value = "olar.br"
        expected = [("olar.br", "br")]
        assert self.matcher.find(value) == expected

    def test_not_br_tld(self):
        value = "olar.bra"
        expected = []
        assert self.matcher.find(value) == expected

        value = "www.mydomain.com"
        expected = []
        assert self.matcher.find(value) == expected

    def test_only_tld(self):
        value = "edu.br"
        expected = [(None, "edu.br")]
        assert self.matcher.find(value) == expected

        value = "Olá, esse é um domínio com.br!"
        expected = [(None, "com.br")]
        assert self.matcher.find(value) == expected

    def test_multiple_domains_tld_and_text(self):
        value = "Olá, mundo. Esse é um link: www.mydomain.com.br (esse é .com.br) e outro: www.example.net - finalizando: www.isp.net.br/path!"
        expected = [("mydomain.com.br", "com.br"), (None, "com.br"), ("isp.net.br", "net.br")]
        assert self.matcher.find(value) == expected

    def test_multiple_domains_multilines(self):
        value = "Olá, mundo.\nEsse é um link: www.mydomain.com.br (esse é .com.br).\nE outro: www.example.net.\nFinalizando: www.isp.net.br/path!"
        expected = [("mydomain.com.br", "com.br"), (None, "com.br"), ("isp.net.br", "net.br")]
        assert self.matcher.find(value) == expected


if __name__ == "__main__":
    import argparse
    import csv
    import io
    import sys


    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    cmd_download = subparsers.add_parser("download")
    cmd_download.add_argument("--print-regexp", action="store_true", help="Print a regexp with BR TLD domain extraction from a domain string")
    cmd_download.add_argument("output_csv_filename", help="CSV filename to save BR TLDs to")

    cmd_filter = subparsers.add_parser("filter")
    cmd_filter.add_argument("--tld-csv", help="CSV with TLDs (when provided, will not scrape registro.br)")
    cmd_filter.add_argument("--tld-csv-encoding", default="utf-8", help="Encoding of input TLD CSV file, if provided")
    cmd_filter.add_argument("--encoding", default="utf-8", help="Encoding of input")
    cmd_filter.add_argument("--input-filename", help="Filename to read data from (if empty, stdin is used instead)")

    args = parser.parse_args()
    command = args.command

    if command == "download":
        filename = Path(args.output_csv_filename)
        print_regexp = args.print_regexp

        with filename.open(mode="w") as fobj:
            writer = None
            tlds = []
            for row in br_tlds():
                if writer is None:
                    writer = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
                tlds.append(row["tld"])
        if print_regexp:
            print(br_domain_tld_regexp(tlds))

    elif command == "filter":
        original_filename = args.input_filename
        filename = Path(original_filename) if original_filename else None
        encoding = args.encoding
        tld_csv = Path(args.tld_csv) if args.tld_csv else None
        tld_csv_encoding = args.tld_csv_encoding

        if filename is not None:
            if not filename.exists():
                print("ERROR: file {repr(original_filename)} not found.", file=sys.stderr)
                exit(1)
            input_fobj = filename.open(encoding=encoding)
            should_close_input_fobj = True
        else:  # Read from stdin
            input_fobj = io.TextIOWrapper(sys.stdin.buffer, encoding=encoding)
            should_close_input_fobj = False

        matcher = BRDomainMatcher(input_csv=tld_csv, encoding=tld_csv_encoding)
        for line in input_fobj:
            line = line.strip()
            if not line:
                continue
            for domain, tld in matcher.find(line):
                if domain:
                    print(domain)
        if should_close_input_fobj:
            fobj.close()
