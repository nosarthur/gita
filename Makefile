dist:
	python setup.py sdist
install:
	pip install dist/gita-0.1.dev0.tar.gz --force-reinstall
test:
	pytest tests
clean:
	git clean -fdx
