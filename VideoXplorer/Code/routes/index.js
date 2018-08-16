var express = require('express');
var passport = require('passport');
var router = express.Router();

/* GET home page. */
router.get('/', function(req, res){
  res.render('home', {user: req.user});
});

//displays our signin page
router.get('/signin', function(req, res){
  res.render('signin');
});

//displays our signup page
router.get('/signup', function(req, res){
  res.render('signup');
});

//sends the request through our local signup strategy, and if successful takes user to catalogue page, otherwise returns then to signin page
router.post('/local-reg', passport.authenticate('local-signup', {
  // successRedirect: '/catalogue/user/',
  failureRedirect: '/signup'
  }), function (req, res) {
    req.session.videos = req.user.videos;
    res.redirect('/catalogue');
  }
);

//sends the request through our local login/signin strategy, and if successful takes user to catalogue page, otherwise returns then to signin page
router.post('/login', passport.authenticate('local-signin', {
  // successRedirect: '/',
  failureRedirect: '/signin'
  }), function (req, res) {
    req.session.videos = req.user.videos;
    res.redirect('/catalogue');
  }
);

//logs user out of site, deleting them from the session, and returns to homepage
router.get('/logout', function(req, res){
  var name = req.user.username;
  console.log("LOGGIN OUT " + req.user.username);
  req.logout();
  res.redirect('/');
  req.session.notice = "You have successfully been logged out " + name + "!";
});

module.exports = router;
