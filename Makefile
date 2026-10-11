.PHONY: docs
docs:
	uv run sphinx-build docs docs/_build

.PHONY: build
build:
	uv build

RangeMessage.xml:
	curl https://www.isbn-international.org/export_rangemessage.xml \
	  -o RangeMessage.xml

# If download failed and you already have the RangeMessage.xml file, then
# run only this target as: make -W RangeMessage.xml ranges.py
ranges.py: RangeMessage.xml FORCE
	uv run --extra ranges python scripts/create-ranges-file.py RangeMessage.xml \
	  > src/prettyisbns/ranges.py
	uv run --extra ranges ruff format src/prettyisbns/ranges.py

FORCE:
