#!/usr/bin/env python
# encoding: utf-8

import os, sys, re
import unittest
import threading
import shutil
import logging
logging.basicConfig(level=logging.DEBUG)
from time import sleep

sys.path.insert(0, os.path.join('.'))
from fsdfs.filesystem import Filesystem


class TestFS(Filesystem):
    
    _rules = {"n":2}
    
    def getReplicationRules(self,file):
        return self._rules
    
    
   
class quotaTests(unittest.TestCase):
    filedb ="memory"
    """ {
        "backend":"mongodb",
        "host":"localhost",
        "db":"fsdfs_test",
        "port":27017
    }"""
    
    def setUp(self):
		
		if os.path.exists("./tests/datadirs"):
			shutil.rmtree("./tests/datadirs")
		os.makedirs("./tests/datadirs")

    def testConflict(self):
        
        
        
        secret = "azpdoazrRR"
        
        nodeA = TestFS({
            "host":"localhost:52342",
            "datadir":"./tests/datadirs/A",
            "secret":secret,
            "resetFileDbOnStart":True,
            "master":"localhost:52342",
            "replicatorIdleTime":2,
            "maxstorage":10,
            "filedb":self.filedb,
            "garbageMinKn":-1
        })
        
        nodeB = TestFS({
            "host":"localhost:52352",
            "datadir":"./tests/datadirs/B",
            "secret":secret,
            "resetFileDbOnStart":True,
            "replicatorIdleTime":2,
            "master":"localhost:52342",
            "maxstorage":10,
            "filedb":self.filedb
        })
        
        nodeC = TestFS({
            "host":"localhost:52362",
            "datadir":"./tests/datadirs/C",
            "secret":secret,
            "resetFileDbOnStart":True,
            "replicatorIdleTime":2,
            "master":"localhost:52342",
            "maxstorage":10,
            "filedb":self.filedb
        })
        
        nodeD = TestFS({
            "host":"localhost:52372",
            "datadir":"./tests/datadirs/D",
            "secret":secret,
            "resetFileDbOnStart":True,
            "replicatorIdleTime":2,
            "master":"localhost:52342",
            "maxstorage":10,
            "filedb":self.filedb
        })
        
        
        
        
        
        nodeA.start()
        nodeB.start()
        nodeC.start()
        
        
        
        nodeA.importFile("tests/fixtures/10b.txt","tests/fixtures/10b.txt")
        
        sleep(4)
        
        self.assertHasFile(nodeA, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeB, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeC, "tests/fixtures/10b.txt")
        self.assertEquals(0,nodeA.getStatus()["df"])
        self.assertEquals(0,nodeB.getStatus()["df"])
        self.assertEquals(0,nodeC.getStatus()["df"])
        
        
        self.assertEquals(1,nodeA.filedb.getKn("tests/fixtures/10b.txt"))
        
        self.assertTrue(nodeA.deleteFile("tests/fixtures/10b.txt"))
        
        self.assertEquals(0,nodeA.filedb.getKn("tests/fixtures/10b.txt"))
        
        nodeA.importFile("tests/fixtures/10b.2.txt","tests/fixtures/10b.2.txt")
        
        sleep(1)
        
        for i in range(0,3):
                
            self.assertHasFile(nodeA, "tests/fixtures/10b.2.txt")
            self.assertHasFile(nodeB, "tests/fixtures/10b.txt")
            self.assertHasFile(nodeC, "tests/fixtures/10b.txt")
            
            self.assertEquals(0,nodeA.getStatus()["df"])
            self.assertEquals(0,nodeB.getStatus()["df"])
            self.assertEquals(0,nodeC.getStatus()["df"])
                
            sleep(1)
        
        
        nodeD.start()
        
        
        sleep(3)
        
        self.assertHasFile(nodeA, "tests/fixtures/10b.2.txt")
        self.assertHasFile(nodeB, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeC, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeD, "tests/fixtures/10b.2.txt")
        
        
        #over-quota import
        imp=nodeA.importFile("tests/fixtures/10b.3.txt","tests/fixtures/10b.3.txt")
        self.assertTrue(imp)
        
        sleep(1)
        
        self.assertEquals(0,nodeA.getStatus()["df"])
        self.assertEquals(0,nodeB.getStatus()["df"])
        self.assertEquals(0,nodeC.getStatus()["df"])
        self.assertEquals(0,nodeD.getStatus()["df"])
        
        self.assertHasFile(nodeA, "tests/fixtures/10b.3.txt")
        self.assertHasFile(nodeB, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeC, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeD, "tests/fixtures/10b.2.txt")
        
        #again, over-quota import
        imp=nodeA.importFile("tests/fixtures/10b.4.txt","tests/fixtures/10b.4.txt")
        self.assertFalse(imp)
        
        #won't work because 10b.3.txt has kn=-1 (garbageMinKn)
        
        self.assertEquals(0,nodeA.getStatus()["df"])
        self.assertEquals(0,nodeB.getStatus()["df"])
        self.assertEquals(0,nodeC.getStatus()["df"])
        self.assertEquals(0,nodeD.getStatus()["df"])
        
        self.assertHasFile(nodeA, "tests/fixtures/10b.3.txt")
        self.assertHasFile(nodeB, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeC, "tests/fixtures/10b.txt")
        self.assertHasFile(nodeD, "tests/fixtures/10b.2.txt")
        
        
        # however, it should work in the future because master should be considered less safe than nodes and 10b.3 should have been 
        # moved off. TODO implement this (-0.000001 in k when on master?)
        
        
        
        nodeA.stop()
        nodeB.stop()
        nodeC.stop()
        nodeD.stop()
        
    
    #doesn't work anymore - should nodes pass their maxstorage so they
    #don't get an oversize file selected?
    def _testSpaceOptimization(self):
        
        secret = "azpdoazrRR"
        
        nodeA = TestFS({
            "host":"localhost:42342",
            "datadir":"./tests/datadirs/A",
            "secret":secret,
            "resetFileDbOnStart":True,
            "replicatorIdleTime":2,
            "master":"localhost:42342",
            "maxstorage":13,
            "filedb":self.filedb
        })
        
        nodeB = TestFS({
            "host":"localhost:42352",
            "datadir":"./tests/datadirs/B",
            "secret":secret,
            "resetFileDbOnStart":True,
            "replicatorIdleTime":2,
            "master":"localhost:42342",
            "maxstorage":100000,
            "filedb":self.filedb
        })
        
        nodeC = TestFS({
            "host":"localhost:42362",
            "datadir":"./tests/datadirs/C",
            "secret":secret,
            "resetFileDbOnStart":True,
            "replicatorIdleTime":2,
            "master":"localhost:42342",
            "maxstorage":12,
            "filedb":self.filedb
        })
        
        nodeD = TestFS({
            "host":"localhost:42372",
            "datadir":"./tests/datadirs/D",
            "secret":secret,
            "resetFileDbOnStart":True,
            "replicatorIdleTime":2,
            "master":"localhost:42342",
            "maxstorage":1,
            "filedb":self.filedb
        })
        
        nodeA.start()
        nodeB.start()
        nodeC.start()
        nodeD.start()
        
        
        
        nodeA.importFile("tests/fixtures/10b.txt","tests/fixtures/10b.txt")
        nodeA.importFile("tests/fixtures/2b.txt","tests/fixtures/2b.txt")
        nodeA.importFile("tests/fixtures/1b.txt","tests/fixtures/1b.txt")
        
        sleep(4)
        
        
        for i in range(0,3):
            
            print "files : %s" % {
                "A":nodeA.filedb.listInNode(nodeA.host),
                "B":nodeA.filedb.listInNode(nodeB.host),
                "C":nodeA.filedb.listInNode(nodeC.host),
                "D":nodeA.filedb.listInNode(nodeD.host)
            }
            self.assertHasFile(nodeA, "tests/fixtures/2b.txt")
            self.assertHasFile(nodeA, "tests/fixtures/10b.txt")
            self.assertHasFile(nodeA, "tests/fixtures/1b.txt")
            
            self.assertHasFile(nodeB, "tests/fixtures/10b.txt")
            self.assertHasFile(nodeB, "tests/fixtures/2b.txt")
            self.assertHasFile(nodeB, "tests/fixtures/1b.txt")
            
            self.assertHasFile(nodeC, "tests/fixtures/10b.txt")
            self.assertHasFile(nodeC, "tests/fixtures/2b.txt")
            
            self.assertHasFile(nodeD, "tests/fixtures/1b.txt")
            
            self.assertEquals(0,nodeA.getStatus()["df"])
            self.assertEquals(0,nodeC.getStatus()["df"])
            self.assertEquals(0,nodeD.getStatus()["df"])
            
            sleep(1)
        
        self.assertTrue(nodeA.deleteFile("tests/fixtures/10b.txt"))
        
        nodeA.importFile("tests/fixtures/10b.2.txt","tests/fixtures/10b.2.txt")
        
        sleep(6)
        
        for i in range(0,3):
                
            print "files : %s" % {
                "A":nodeA.filedb.listInNode(nodeA.host),
                "B":nodeA.filedb.listInNode(nodeB.host),
                "C":nodeA.filedb.listInNode(nodeC.host),
                "D":nodeA.filedb.listInNode(nodeD.host)
            }
            
            self.assertHasFile(nodeA, "tests/fixtures/10b.2.txt")
            self.assertHasFile(nodeA, "tests/fixtures/1b.txt")
            self.assertHasFile(nodeA, "tests/fixtures/2b.txt")
            
            self.assertHasFile(nodeB, "tests/fixtures/1b.txt")
            self.assertHasFile(nodeB, "tests/fixtures/2b.txt")
            self.assertHasFile(nodeB, "tests/fixtures/10b.txt")
            self.assertHasFile(nodeB, "tests/fixtures/10b.2.txt")
            
            self.assertHasFile(nodeC, "tests/fixtures/2b.txt")
            self.assertHasFile(nodeC, "tests/fixtures/10b.txt")
            
            self.assertHasFile(nodeD, "tests/fixtures/1b.txt")
            
            self.assertEquals(0,nodeA.getStatus()["df"])
            self.assertEquals(0,nodeC.getStatus()["df"])
            self.assertEquals(0,nodeD.getStatus()["df"])
            
            sleep(1)
            
        
        nodeA.stop()
        nodeB.stop()
        nodeC.stop()
        nodeD.stop()
        
        
    def assertHasFile(self,node,destpath):
        self.assertTrue(os.path.isfile(node.getLocalFilePath(destpath)))
        if os.path.isfile(node.getLocalFilePath(destpath)):
            self.assertEquals(open(node.getLocalFilePath(destpath)).read(),open(destpath).read())
        
        
if __name__ == '__main__':
    unittest.main()
