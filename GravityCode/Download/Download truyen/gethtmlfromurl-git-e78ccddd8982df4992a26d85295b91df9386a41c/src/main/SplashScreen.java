package main;

import java.awt.Color;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.EventQueue;
import java.awt.Font;
import java.awt.Toolkit;
import java.util.Locale;

import javax.swing.ImageIcon;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.SwingConstants;
import javax.swing.WindowConstants;
import javax.swing.border.EmptyBorder;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonValue;
import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.SettingOption;
import resource.text.Messages;

public class SplashScreen extends JDialog {

	/**
	 * Splash Screen
	 */
	private static final long serialVersionUID = 1L;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			@Override
			public void run() {
				try {
					SplashScreen frame = new SplashScreen();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private JPanel contentPane;

	JLabel lblStatus;

	/**
	 * Create the frame.
	 */
	public SplashScreen() {
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		setUndecorated(true);
		setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
		setResizable(false);
		setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		setBounds(100, 100, 472, 146);
		contentPane = new JPanel();
		contentPane.setBackground(new Color(0, 102, 51));
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));
		setContentPane(contentPane);
		contentPane.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("127px"),
						ColumnSpec.decode("max(150dlu;default)"), ColumnSpec.decode("max(64dlu;default):grow"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { RowSpec.decode("32px"), RowSpec.decode("34px"), FormSpecs.DEFAULT_ROWSPEC,
						RowSpec.decode("30px:grow"), RowSpec.decode("14px"), FormSpecs.LINE_GAP_ROWSPEC, }));

		JLabel lblTitle = new JLabel("");
		lblTitle.setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
		lblTitle.setDisabledIcon(null);
		lblTitle.setIconTextGap(1);
		lblTitle.setHorizontalAlignment(SwingConstants.LEFT);
		lblTitle.setForeground(new Color(0, 255, 51));
		lblTitle.setIcon(new ImageIcon(SplashScreen.class.getResource("/resource/box-128.png")));
		lblTitle.setFont(new Font("Tahoma", Font.PLAIN, 20));
		contentPane.add(lblTitle, "2, 1, 1, 4, fill, fill");

		JLabel lblAppName = new JLabel(Messages.getString("SplashScreen.lblAppName.txt"));
		lblAppName.setIconTextGap(1);
		lblAppName.setHorizontalAlignment(SwingConstants.LEFT);
		lblAppName.setForeground(new Color(0, 255, 51));
		lblAppName.setFont(new Font("Tahoma", Font.PLAIN, 20));
		contentPane.add(lblAppName, "3, 2, 2, 1, default, bottom");

		JLabel lblGethtmlfromurl = new JLabel(Messages.getGlobalString("app.name"));
		lblGethtmlfromurl.setIconTextGap(1);
		lblGethtmlfromurl.setHorizontalAlignment(SwingConstants.LEFT);
		lblGethtmlfromurl.setForeground(new Color(0, 255, 51));
		lblGethtmlfromurl.setFont(new Font("Tahoma", Font.BOLD, 13));
		contentPane.add(lblGethtmlfromurl, "3, 3, left, fill");

		JLabel lblVersion_1 = new JLabel(String.format(Messages.getGlobalString("app.version"), CommonValue.APP_VERSION));
		lblVersion_1.setFont(new Font("Tahoma", Font.ITALIC, 11));
		lblVersion_1.setForeground(new Color(0, 255, 0));
		contentPane.add(lblVersion_1, "4, 3, right, top");

		lblStatus = new JLabel(String.format(Messages.getString("SplashScreen.lblStatus.text"), ""));
		lblStatus.setForeground(new Color(0, 255, 51));
		contentPane.add(lblStatus, "2, 5, 2, 1, fill, bottom");

		JLabel lblAuthor = new JLabel("By Mkbyme");
		lblAuthor.setFont(new Font("Tahoma", Font.ITALIC, 12));
		lblAuthor.setForeground(new Color(0, 255, 51));
		contentPane.add(lblAuthor, "4, 5, right, top");
		// set center start position
		Dimension dimension = Toolkit.getDefaultToolkit().getScreenSize();
		int startX = (dimension.width / 2) - getWidth() / 2;
		int startY = (dimension.height / 2) - getHeight() / 2;
		setLocation(startX, startY);
		setAlwaysOnTop(false);
	}

	public void setStatus(String text) {
		lblStatus.setText(String.format(Messages.getString("SplashScreen.lblStatus.text"), text));
	}

}
