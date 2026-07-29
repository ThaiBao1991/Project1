/**
 * 
 */
package common;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.text.DateFormat;
import java.util.Date;

import log.CommonLog;
import main.JExceptionDialog;

/**
 * @author nxcuo
 *
 */
public class CommonExceptionHandle {

	/**
	 * flag, check that has exception was show on.
	 */
	public static Boolean IsHasException = false;

	public static void HandleException(Exception ex, String desciption) {

		CommonExceptionHandle.IsHasException = true;
		DateFormat df = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT);
		StringBuilder sb = new StringBuilder();

		if (ex instanceof SocketTimeoutException || ex instanceof ConnectException) {
			sb.append("Trang quá chậm để phản hồi.\r\n");
			sb.append("Thử thiết đặt lại thời gian chờ và khoảng nghỉ trong menu:\r\n");
			sb.append("Tệp > Cài Đặt: Khoảng nghỉ 3500, Thời gian chờ: 120 xem nhé.\r\n");
		} else {
			sb.append("OCCUR: " + desciption + "\n");
			sb.append("TIME: " + df.format(new Date()) + "\n");
			sb.append("CONTENT: " + ex + "\n");
			sb.append("STACKTRACE:\n");
			for (StackTraceElement line : ex.getStackTrace()) {
				sb.append(line.toString() + "\n");
			}
		}
		CommonLog.logError(ex);
		new JExceptionDialog(sb.toString()).setVisible(true);
	}
}
