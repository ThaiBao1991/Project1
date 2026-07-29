/**
 * 
 */
package log;

import java.awt.Color;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;

import javax.swing.JTextArea;

import common.Enumeration;
import common.Enumeration.LogType;
import common.Enumeration.UIType;
import main.Main;

/**
 * @author nxcuo print log into UI
 */
public class CommonUILog {

	/**
	 * pattern of log data
	 */
	private static String _logPatternData = "[%s]%s\r\n";

	/**
	 * Log info mesasage to UI
	 * 
	 * @param message
	 */
	public static void info(String message) {
		writeLogToUI("[INF]" + message, Enumeration.LogType.Info, UIType.MainWindow, null);
	}

	/**
	 * Log info mesasage to UI
	 * 
	 * @param message
	 */
	public static void info(String message, UIType type, JTextArea txtLog) {
		writeLogToUI("[INF]" + message, Enumeration.LogType.Info, type, txtLog);
	}

	/**
	 * Log error mesasage to UI
	 * 
	 * @param message
	 */
	public static void error(String message) {
		writeLogToUI("[ERR]" + message, Enumeration.LogType.Error, UIType.MainWindow, null);
	}

	/**
	 * Log error mesasage to UI
	 * 
	 * @param message
	 */
	public static void error(String message, UIType type, JTextArea txtLog) {
		writeLogToUI("[ERR]" + message, Enumeration.LogType.Error, type, txtLog);
	}

	/**
	 * Log warning mesasage to UI
	 * 
	 * @param message
	 */
	public static void warn(String message) {
		writeLogToUI("[WAN]" + message, Enumeration.LogType.Warning, UIType.MainWindow, null);
	}

	/**
	 * Log warning mesasage to UI
	 * 
	 * @param message
	 */
	public static void warn(String message, UIType type, JTextArea txtLog) {
		writeLogToUI("[WAN]" + message, Enumeration.LogType.Warning, type, txtLog);
	}

	/**
	 * Do print log to UI
	 * 
	 * @param message
	 * @param logType
	 * @param uiType
	 */
	private static void writeLogToUI(String message, Enumeration.LogType logType, Enumeration.UIType uiType,
			JTextArea txtLog) {

		try {
			Date date = Calendar.getInstance().getTime();
			SimpleDateFormat dateFormat = new SimpleDateFormat("yyyyMMdd");
			// log data file
			dateFormat.applyPattern("yyyy-MM-dd HH:mm:ss");
			String content = String.format(_logPatternData, dateFormat.format(date), message);
			if (txtLog == null) {
				switch (uiType) {

				case MainWindow:
					if (Main.window != null && Main.window.txtLog != null) {
						txtLog = Main.window.txtLog;

					}
					break;
				case ManualUIWindow:
					if (Main.manualGetUI != null && Main.manualGetUI.txtLog != null) {
						txtLog = Main.manualGetUI.txtLog;
					}
					break;
				case PageConfigWindow:
					if (Main.pageConfigManager != null && Main.pageConfigManager.txtLog != null) {
						txtLog = Main.pageConfigManager.txtLog;
					}
					break;
				default:
					break;
				}

			}
			if (txtLog != null) {
				setLogForeground(txtLog, logType);
				txtLog.append(content);
				txtLog.setCaretPosition(txtLog.getDocument().getLength());
			}
		} catch (Exception e) {
			CommonLog.logError(e);
			e.printStackTrace();
		}

	}

	/**
	 * set foreground for JTextArea
	 * 
	 * @param txtLog
	 *            - TextArea
	 * @param logType
	 *            - type
	 */
	private static void setLogForeground(JTextArea txtLog, LogType logType) {

		switch (logType) {
		// case Info:
		// txtLog.setForeground(Color.GREEN);
		// break;
		// case Warning:
		// txtLog.setForeground(Color.ORANGE);
		// break;
		// case Error:
		// txtLog.setForeground(Color.RED);
		// break;
		default:
			txtLog.setForeground(Color.GREEN);
			break;
		}

	}
}
