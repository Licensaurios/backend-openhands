deb:
	docker build -f Dockerfile --target builder -t sholsapp/backend-learnify-builder .
	docker create --cidfile .tmp-docker-container-id sholsapp/backend-learnify-builder
	xargs -I {} docker cp -a "{}:/build/backend-learnify_0.1-1_amd64.deb" . < .tmp-docker-container-id
	xargs -I {} docker rm -f "{}" < .tmp-docker-container-id
	rm .tmp-docker-container-id

docker:
	docker build -t sholsapp/backend-learnify:0.1 .
	docker run --cidfile .backend-learnify-container-id --publish 8080:8080 --detach sholsapp/backend-learnify:0.1

clean:
	git clean -fxd -e infra

