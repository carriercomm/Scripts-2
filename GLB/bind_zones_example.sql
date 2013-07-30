-- MySQL dump 10.13  Distrib 5.1.69, for redhat-linux-gnu (x86_64)
--
-- Host: localhost    Database: bind_zones
-- ------------------------------------------------------
-- Server version       5.1.69

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `glb_lbaas_rackspace_net`
--

DROP TABLE IF EXISTS `glb_lbaas_rackspace_net`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `glb_lbaas_rackspace_net` (
  `name` varchar(255) DEFAULT NULL,
  `ttl` int(11) DEFAULT NULL,
  `rdtype` varchar(255) DEFAULT NULL,
  `rdata` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `glb_lbaas_rackspace_net`
--

LOCK TABLES `glb_lbaas_rackspace_net` WRITE;
/*!40000 ALTER TABLE `glb_lbaas_rackspace_net` DISABLE KEYS */;
INSERT INTO `glb_lbaas_rackspace_net` VALUES ('glb.lbaas.rackspace.net',259200,'SOA','glb1.glb.lbaas.rackspace.net. info.glb.lbaas.rackspace.net. 200309181 28800 7200 86400 28800'),('glb.lbaas.rackspace.net',259200,'NS','glb1.glb.lbaas.rackspace.net.'),('customer2.glb.lbaas.rackspace.net',259200,'A','119.9.13.113'),('customer1.glb.lbaas.rackspace.net',259200,'A','166.78.106.91'),('glb1.glb.lbaas.rackspace.net',259200,'A','162.209.91.20'),('customer2.glb.lbaas.rackspace.net',259200,'A','166.78.106.91'),('customer1.glb.lbaas.rackspace.net',259200,'A','119.9.13.113');
/*!40000 ALTER TABLE `glb_lbaas_rackspace_net` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-07-30 18:48:06
