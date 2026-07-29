package common;

import java.awt.Component;
import java.awt.event.FocusEvent;

import javax.swing.JFormattedTextField;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;

/**
 * All method process UI
 * 
 * @author mkbyme Jan 27, 2019
 *
 */
public class CommonUIFunction {
	/**
	 * selec value on focus
	 * 
	 * @param focusEvent
	 */
	public static void doSelectAllOnFocusJSpinner(FocusEvent focusEvent) {
		// works for editable
		final Component c = focusEvent.getComponent();
		if (c instanceof JFormattedTextField) {
			SwingUtilities.invokeLater(new Runnable() {
				@Override
				public void run() {
					((JFormattedTextField) c).setText(((JFormattedTextField) c).getText());
					((JFormattedTextField) c).selectAll();
				}
			});
		} else if (c instanceof JTextField) {
			SwingUtilities.invokeLater(new Runnable() {
				@Override
				public void run() {
					((JTextField) c).setText(((JTextField) c).getText());
					((JTextField) c).selectAll();
				}
			});
		}
	}
}
