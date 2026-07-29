/**
 * 
 */
package log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;

import common.CommonValue;
import common.Enumeration.LogType;

/**
 * @author nxcuo write log
 */
public class CommonLog {
	
	
	/**
	 * folder name save log files in
	 */
	private static String _folderLog = "Log";
	/**
	 * name pattern log {Date}_{Type}.txt
	 */
	private static String _logPatternFileName = "%s_%s.txt";// ex:
															// 20180907_Error.txt
	/**
	 * pattern of log data
	 */
	private static String _logPatternData = "[%s]: %s\r\n";// ex [21:01:27 -
	// 07/09/2018]
	// Cannot download from
	// truyenyy.com.

	/**
	 * Write common info
	 * 
	 * @param message
	 */
	public static void logInfo(String message) {
		writeLog(message, LogType.Info);
	}

	/**
	 * Write exception log
	 * 
	 * @param e
	 */
	public static void logError(Exception e) {
		try {
			StringWriter sw = new StringWriter();
			PrintWriter pw = new PrintWriter(sw);
			e.printStackTrace(pw);
			String stackTrace = sw.toString();
			writeLog("Message: " + e.getMessage() + ", StackTrace: " + stackTrace, LogType.Error);
		} catch (Exception e1) {
			e1.printStackTrace();
		}
	}

	/**
	 * Write exception log
	 * 
	 * @param message
	 */
	public static void logError(String message) {
		writeLog(message, LogType.Error);
	}

	/**
	 * Warning log
	 * 
	 * @param message
	 */
	public static void logWarning(String message) {
		writeLog(message, LogType.Warning);
	}

	/**
	 * Process create, open and append log to current date log
	 * 
	 * @param message
	 */
	private static void writeLog(String message, LogType logType) {
		Date date = Calendar.getInstance().getTime();
		SimpleDateFormat dateFormat = new SimpleDateFormat("yyyyMMdd");
		String fileName = String.format(_logPatternFileName, dateFormat.format(date), logType.toString());
		// log data file
		dateFormat.applyPattern("HH:mm:ss:SSS");

		String logFolderPath = String.format("%s\\%s", CommonValue.getAppJARFile().getParentFile().getPath(),
				_folderLog);
		
		if (logFolderPath.contains(";")) {
			logFolderPath = String.format("%s\\%s", CommonValue.getJarPath(), _folderLog);
		}

		fileName = String.format("%s\\%s", logFolderPath, fileName);

		File folder = new File(logFolderPath);
		if (!folder.exists()) {
			folder.mkdirs();
		}

		File logFile = new File(fileName);
		OutputStreamWriter osw = null;
		Boolean isCreated = true;
		if (!logFile.exists()) {
			try {
				logFile.createNewFile();
			} catch (IOException e) {
				isCreated = false;
				e.printStackTrace();
			}
		}

		if (isCreated) {
			try {
				osw = new OutputStreamWriter(new FileOutputStream(logFile, true), "UTF-8");
				osw.write(String.format(_logPatternData, dateFormat.format(date), message));
				osw.close();
			} catch (IOException e) {
				e.printStackTrace();
			} finally {
				if (osw != null) {
					try {
						osw.close();
					} catch (IOException e) {
						e.printStackTrace();
					}
				}
			}

		}
	}
}
