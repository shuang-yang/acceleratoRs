var bcrypt = require('bcryptjs'),
    Q = require('q'); 

var docdbUtils = require('../models/docdbUtils');

function DbManager(documentDBClient, databaseId, collectionId) {
    this.client = documentDBClient;
    this.databaseId = databaseId;
    this.collectionId = collectionId;
  
    this.database = null;
    this.collection = null;
}

DbManager.prototype = {
    init: function(callback) {
        var self = this;
    
        docdbUtils.getOrCreateDatabase(self.client, self.databaseId, function(err, db) {
          if (err) {
            callback(err);
          }
    
          self.database = db;
          docdbUtils.getOrCreateCollection(self.client, self.database._self, self.collectionId, function(err, coll) {
            if (err) {
              callback(err);
            }
    
            self.collection = coll;
          });
        });
    },

    //used in local-signup strategy
    localReg: function (username, password, blobName, blobKey, dbEndpoint, dbKey, searchName, searchKey, cvKey, cvURL) {
        var self = this;
        var deferred = Q.defer();

        var query = {
            "query": "SELECT * FROM r WHERE r.username=@username",
            "parameters": [
                {"name": "@username", "value": username}
            ]
        };

        self.client.queryDocuments(self.collection._self, query).toArray(function(err, results) {
            if (results != null && results.length > 0) {
                console.log("USERNAME ALREADY EXISTS:", results[0].username);
                deferred.resolve(false); // username exists
            } else  {
                var hash = bcrypt.hashSync(password, 8);
                var user = {
                    "username": username,
                    "password": hash,
                    "blobName": blobName,
                    "blobKey": blobKey,
                    "dbEndpoint": dbEndpoint,
                    "dbKey": dbKey,
                    "searchName": searchName,
                    "searchKey": searchKey,
                    "cvKey": cvKey,
                    "cvURL": cvURL,
                    "videos": {}
                };

                console.log("CREATING USER:", username);

                self.client.createDocument(self.collection._self, user, function(err, doc) {
                    if (err) {
                        throw err;
                    } else {
                        deferred.resolve(user);
                    }
                });
            }
        });

        return deferred.promise;
    },


    //check if user exists
        //if user exists check if passwords match (use bcrypt.compareSync(password, hash); // true where 'hash' is password in DB)
        //if password matches take into website
    //if user doesn't exist or password doesn't match tell them it failed
    localAuth: function (username, password) {
        var self = this;
        var deferred = Q.defer();

        var query = {
            "query": "SELECT * FROM r WHERE r.username=@username",
            "parameters": [
                {"name": "@username", "value": username}
            ]
        };

        self.client.queryDocuments(self.collection._self, query).toArray(function(err, results) {
            if (results == undefined || results.length == 0) {
                console.log("USERNAME NOT FOUND:", username);
                deferred.resolve(false);
            } else {
                var hash = results[0].password;

                console.log("FOUND USER: " + results[0].username);

                if (bcrypt.compareSync(password, hash)) {
                    deferred.resolve(results[0]);
                } else {
                    console.log("AUTHENTICATION FAILED");
                    deferred.resolve(false);
                }
            }
        });

        return deferred.promise;
    },

    updateField: function(itemId, idFieldName, updateFieldName, newValue, callback) {
        var self = this;

        self.getItem(itemId, idFieldName, function(err, doc) {
            if (err) {
                callback(err);
            } else {
                doc[updateFieldName] = newValue;
                self.client.replaceDocument(doc._self, doc, function(err, replaced) {
                    if (err) {
                        callback(err);
                    } else {
                        callback(null);
                    }
                });
            }
        });
    },

    getItem: function(username, fieldName, callback) {
        var self = this;

        var query = {
            "query": "SELECT * FROM r WHERE r.username=@username",
            "parameters": [
                {"name": "@username", "value": username}
            ]
        };
        console.log("collection link: " + self.collection._self);
        self.client.queryDocuments(self.collection._self, query).toArray(function(err, results) {
            if (err) {
                callback(err);
            } else {
                callback(null, results[0]);
            }
        });
    }
};

module.exports = DbManager;