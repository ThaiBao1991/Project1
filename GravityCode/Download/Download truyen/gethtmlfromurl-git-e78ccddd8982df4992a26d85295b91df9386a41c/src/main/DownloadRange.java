package main;

import java.awt.Component;
import java.awt.EventQueue;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusAdapter;
import java.awt.event.FocusEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.Locale;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSpinner;
import javax.swing.SpinnerNumberModel;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;

import org.eclipse.wb.swing.FocusTraversalOnArray;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonUIFunction;
import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.SettingOption;
import resource.text.Messages;

/**
 * frm show a dialog to prompt range of download chapter created by mkbyme
 * 10/11/2016
 */
public class DownloadRange extends JDialog {

	/**
	 * declare
	 */
	private static final long serialVersionUID = 1L;
	public static int start = 0;
	public static int end = 0;
	public static Boolean visiable = false;
	public static Boolean setComplete = false;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			@Override
			public void run() {
				try {
					DownloadRange frame = new DownloadRange();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	public static void SetValue(int start, int end, Boolean visable) {
		DownloadRange.start = start;
		DownloadRange.end = end;
		DownloadRange.visiable = visable;
		setComplete = false;
	}

	private JPanel contentPane;

	public JSpinner spinnerEnd;

	public JSpinner spinnerStart;

	private JButton btnDownload;

	/**
	 * Create the frame.
	 */
	public DownloadRange() {
		setType(Type.POPUP);
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		setIconImage(Toolkit.getDefaultToolkit().getImage(DownloadRange.class.getResource("/resource/box-16.png")));
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if ((int) spinnerEnd.getValue() < (int) spinnerStart.getValue()) {
					DownloadRange.start = -1;
					int confirm = JOptionPane.showOptionDialog(null,
							Messages.getGlobalString("notify.chapterNumberEndMustBeBiggerThanStart"),
							Messages.getGlobalString("title.notice"),
							JOptionPane.YES_NO_OPTION, JOptionPane.WARNING_MESSAGE, null, new String[] {
									Messages.getGlobalString("btn.reinput"), Messages.getGlobalString("btn.skip") },
							Messages.getGlobalString("btn.skip"));
					if (confirm == JOptionPane.NO_OPTION) {
						setVisible(false);
						DownloadRange.setComplete = true;
						dispose();
					}

				} else {
					DownloadRange.start = (int) spinnerStart.getValue();
					DownloadRange.end = (int) spinnerEnd.getValue();
					setVisible(false);
					DownloadRange.setComplete = true;
				}

			}
		});
		setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
		setAlwaysOnTop(true);
		setTitle(Messages.getString("DownloadRange.this.title")); //$NON-NLS-1$
		setResizable(false);
		setBounds(100, 100, 309, 124);
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			e2.printStackTrace();
		}
		contentPane = new JPanel();
		contentPane.setFocusable(false);
		contentPane.setFocusTraversalKeysEnabled(false);
		contentPane.setBorder(null);
		setContentPane(contentPane);
		contentPane.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("left:61px"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("109px:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.LINE_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						RowSpec.decode("23px"), FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("default:grow"),
						FormSpecs.LINE_GAP_ROWSPEC, }));

		JLabel lblNewLabel = new JLabel(Messages.getString("DownloadRange.lblNewLabel.text")); //$NON-NLS-1$
		contentPane.add(lblNewLabel, "2, 2, right, center");

		spinnerStart = new JSpinner();
		spinnerStart.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent arg0) {
				CommonUIFunction.doSelectAllOnFocusJSpinner(arg0);
			}
		});
		lblNewLabel.setLabelFor(spinnerStart);
		spinnerStart.setModel(new SpinnerNumberModel(new Integer(1), new Integer(1), null, new Integer(1)));
		contentPane.add(spinnerStart, "4, 2, fill, center");

		JLabel lblTo = new JLabel(Messages.getString("DownloadRange.lblTo.text")); //$NON-NLS-1$
		contentPane.add(lblTo, "2, 4, right, center");

		spinnerEnd = new JSpinner();
		lblTo.setLabelFor(spinnerEnd);
		spinnerEnd.setModel(new SpinnerNumberModel(new Integer(2), new Integer(2), null, new Integer(1)));
		contentPane.add(spinnerEnd, "4, 4, fill, center");

		btnDownload = new JButton(Messages.getString("DownloadRange.btnDownload.text"));
		btnDownload.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				DownloadRange.setComplete = false;
				DownloadRange.start = (int) spinnerStart.getValue();
				DownloadRange.end = (int) spinnerEnd.getValue();
				Boolean isDispose = true;
				if (DownloadRange.end < DownloadRange.start) {
					JOptionPane.showMessageDialog(null,
							Messages.getGlobalString("notify.chapterNumberEndMustBeBiggerThanStart"));
					isDispose = false;
				}
				// if allow dispose
				if (isDispose) {
					DownloadRange.setComplete = true;
					setVisible(false);
					dispose();
				}
			}
		});
		contentPane.add(btnDownload, "4, 6, fill, fill");
		contentPane.setFocusTraversalPolicy(
				new FocusTraversalOnArray(new Component[] { spinnerStart, spinnerEnd, btnDownload }));

		// default when create frame
		DownloadRange.setComplete = false;
		DownloadRange.visiable = true;
	}
}
