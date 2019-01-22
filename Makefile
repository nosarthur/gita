.PHONY: dist test install clean twine

test: clean
	pytest tests --cov=./gita $(TEST_ARGS) -n=auto
dist:
	python3 setup.py sdist
twine:
	twine upload dist/*
install:
	# pip3 install dist/gita-0.1.tar.gz --force-reinstall
	pip3 install -e .
clean:
	git clean -fdx
