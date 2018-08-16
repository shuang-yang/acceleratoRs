// Search result route module
var express = require('express');
var router = express.Router();

// Controller for search
var search_controller = require('../controllers/searchController');

router.get('/:id', function (req, res) {
	var url = req.query.url != undefined ? req.query.url : req.session.user.videos[req.params.id].url;
	if (req.query.frames != undefined) {
		var resultsByRel = JSON.parse(req.query.frames);
		// console.log('results: ' + resultsByRel);
		res.render('video', {resultsByRel: resultsByRel, resultsByTime:[], url: url});
	} else if (req.query.term != undefined) {
		search_controller.search_result_video(req, res);
	} else {
		res.render('video', {resultsByRel: [], resultsByTime:[], url: url, searchName: req.query.searchName, searchKey: req.query.searchKey});
	}
});

module.exports = router;