SELECT * FROM billboard_hot_100.hot100;CREATE DATABASE `billboard_hot_100` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin */;
CREATE TABLE `hot100` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `song` varchar(80) DEFAULT NULL,
  `artist` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  UNIQUE KEY `unique_pair` (`artist`,`song`),
  KEY `song` (`song`),
  KEY `artist` (`artist`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
