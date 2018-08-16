// Catalogue route module
var express = require('express');
var router = express.Router();

// Controller for search
var search_controller = require('../controllers/searchController');

var config = require('../config');
var DocumentDBClient = require('documentdb').DocumentClient;
var DbManager = require('../controllers/DbManager');
var docDbClient = new DocumentDBClient(config.host, {
	masterKey: config.authKey
	});
var dbManager = new DbManager(docDbClient, config.databaseId, config.collectionId);
dbManager.init(function(err) { if(err) throw err; });

router.get('/', function (req, res) {
	if (req.query.term != undefined) {
		search_controller.search_result_catalogue(req, res);
	} else {
		var videos = req.session.videos;
		console.log('videos: ' + videos);
		dbManager.getItem(req.session.user.username, 'username', function (err, doc) {
			if (err) {
				throw err;
			} else {
				console.log("got new videos! " + doc.videos);
				videos = doc.videos;
			}
		});
		res.render('catalogue', {videos: videos});
	}
});

module.exports = router;