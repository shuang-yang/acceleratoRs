var express = require('express');
var fileUpload = require('express-fileupload');
var async = require('async');
var router = express.Router();

router.use(fileUpload());

var upload_controller = require('../controllers/uploadController');

/* GET users listing. */
router.get('/', function(req, res) {
  res.render('upload');
});

router.post('/', function(req, res) {
  var blobAccountName = req.query.blobAccountName == undefined ? req.session.user.blobName : req.query.blobAccountName;
  var blobAccountKey = req.query.blobKey == undefined ? req.session.user.blobKey: req.query.blobKey;
  var cosmosdbEndpoint = req.query.dbEndpoint == undefined ? req.session.user.dbEndpoint : req.query.dbEndpoint;
  var cosmosdbMasterkey = req.query.dbKey == undefined ? req.session.user.dbKey : req.query.dbKey;
  var cvKey = req.query.cvKey == undefined ? req.session.user.cvKey : req.query.cvKey;
  var cvURL = req.query.cvURL == undefined ? req.session.user.cvURL : req.query.cvURL;
  var azureSearchName = req.query.azureSearchName == undefined ? req.session.user.searchName : req.query.azureSearchName ;
  var azureSearchKey = req.query.azureSearchKey == undefined ? req.session.user.searchKey : req.query.azureSearchKey;
  var startTime = req.body.startTime;
  var endTime = req.body.endTime;
  var sampleRate = req.body.sampleRate * 1000;
  if (!req.files)
    return res.status(400).send('No files uploaded.');
  var videoFile = req.files.videoFile;
  var videoFileRootPath = './public/videos/';
  var videoFileName = videoFile.name;
  var userId = req.session.user.id;

  videoFile.mv(videoFileRootPath + videoFileName, function (err) {
    if (err)
      return res.status(500).send(err);
    var options = {
      // pythonPath: 've-env/bin/python3.6',
      args:
      [
        blobAccountName,
        blobAccountKey,
        cosmosdbEndpoint,
        cosmosdbMasterkey,
        cvKey,
        cvURL,
        azureSearchName,
        azureSearchKey,
        startTime,
        endTime,
        sampleRate,
        videoFileRootPath,
        videoFileName,
        userId
      ]
    };

    videoFileNameNoExtension = videoFileName.split(".")[0];
    upload_controller.handle_upload(req, res, options, azureSearchName, azureSearchKey);
    // TODO - delete local video file
  });
});

module.exports = router;
