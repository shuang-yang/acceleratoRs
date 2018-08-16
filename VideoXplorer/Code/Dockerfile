
FROM nikolaik/python-nodejs:latest

ENV NODE_ENV production
WORKDIR /usr/src/app
COPY ["package.json", "package-lock.json*", "npm-shrinkwrap.json*", "./"]
RUN npm install --production --silent && mv node_modules ../
COPY . .
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 3000
CMD npm start