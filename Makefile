.PHONY: dist test install clean twine

dist:
	python3 setup.py sdist
twine:
	twine upload dist/*
install:
	# pip3 install dist/gita-0.1.tar.gz --force-reinstall
	pip3 install -e .
test: clean
	pytest tests --cov=./gita $(TEST_ARGS)
clean:
	git clean -fdx
