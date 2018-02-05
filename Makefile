dist:
	python3 setup.py sdist
install:
	pip3 install dist/gita-0.1.dev0.tar.gz --force-reinstall
test:
	pytest tests --cov=./gita
clean:
	git clean -fdx
