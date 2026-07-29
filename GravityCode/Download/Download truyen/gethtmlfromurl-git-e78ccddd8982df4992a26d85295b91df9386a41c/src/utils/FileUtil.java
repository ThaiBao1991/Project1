package utils;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import mk.constant.Constant;

public class FileUtil {

	/**
	 * delete temp file
	 * 
	 * @author mkbyme Oct 15, 2017
	 */
	public static void deleteOldFiles() {
		Path ptemp = Paths.get(System.getProperty("java.io.tmpdir"));
		if (Files.exists(ptemp)) {
			try (DirectoryStream<Path> stream = Files.newDirectoryStream(ptemp, Constant.TMP_PREFIX + "*")) {
				for (Path entry : stream) {
					// delete all sub folder and files content
					delete(entry);
				}

			} catch (IOException x) {
				x.printStackTrace();
			}
		}
	}

	/**
	 * delete folder and all file content
	 * 
	 * @param path
	 *            - folder path
	 * @author mkbyme Oct 15, 2017
	 */
	private static void delete(Path path) {
		if (path != null) {
			try {
				// delete sub folder/files
				deleteRecursive(path);
				// delete current folder/files
				Files.delete(path);
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}

	/**
	 * delete folder and all file content recursive
	 * 
	 * @param path
	 *            - folder path
	 * @author mkbyme Oct 15, 2017
	 */
	private static void deleteRecursive(Path path) {
		if (path != null) {
			try {
				if (path.toFile().isDirectory() && path.toFile().list().length > 0) {
					try (DirectoryStream<Path> stream = Files.newDirectoryStream(path, "*")) {
						for (Path entry : stream) {
							deleteRecursive(entry);
						}
					}
				} else {
					Files.delete(path);
				}
			} catch (IOException x) {
				x.printStackTrace();
			}
		}
	}
}
