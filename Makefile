.PHONY: dist test install clean twine auto-completion

install:
	pip3 install -e .
uninstall:
	pip3 uninstall -e .
test:
	pytest tests --cov=./gita $(TEST_ARGS) -n=auto -vv
dist:
	python3 setup.py sdist
twine:
	twine upload dist/*
clean:
	git clean -fdx
auto-completion:
	@ mkdir -p auto-completion/bash
	@ mkdir -p auto-completion/zsh
	@ mkdir -p auto-completion/fish
	register-python-argcomplete gita -s bash > auto-completion/bash/.gita-completion.bash
	register-python-argcomplete gita -s zsh > auto-completion/zsh/_gita
	register-python-argcomplete gita -s fish > auto-completion/fish/gita.fish
