.PHONY: dist test install clean

dist:
	python3 setup.py sdist
install:
	# pip3 install dist/gita-0.1.tar.gz --force-reinstall
	pip3 install -e .
test:
	pytest tests --cov=./gita $(TEST_ARGS)
clean:
	git clean -fdx
