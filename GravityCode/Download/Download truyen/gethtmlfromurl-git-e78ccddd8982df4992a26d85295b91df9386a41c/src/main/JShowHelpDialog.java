package main;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.Locale;

import javax.swing.GroupLayout;
import javax.swing.GroupLayout.Alignment;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.LayoutStyle.ComponentPlacement;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.WindowConstants;
import javax.swing.border.EmptyBorder;

import common.CommonExceptionHandle;
import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import resource.text.Messages;

public class JShowHelpDialog extends JDialog {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		try {
			JShowHelpDialog dialog = new JShowHelpDialog();
			dialog.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
			dialog.setVisible(true);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	private final JPanel contentPanel = new JPanel();
	String _error = "";
	String _title = "";
	String _message = "";
	EnumConfigKey _configKey = EnumConfigKey.SHOW_TIPS_ON_DOWNLOAD_FAILED;

	private JTextArea txtText;

	public JShowHelpDialog() {
		init();
	}

	/**
	 * Create the dialog.
	 */

	public JShowHelpDialog(EnumConfigKey configKey, String message, String title) {
		this._configKey = configKey;
		this._message = message;
		this._title = title;
		init();
		txtText.setText(message);
		setVisible(true);
	}

	private void init() {
		setType(Type.POPUP);
		setAlwaysOnTop(true);
		setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
			Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
		}
		setIconImage(Toolkit.getDefaultToolkit().getImage(JShowHelpDialog.class.getResource("/resource/box-32.png")));
		setTitle(Messages.getString("JShowHelpDialog.this.title")); //$NON-NLS-1$
		if (!this._title.isEmpty()) {
			setTitle(_title);
		}
		setBounds(100, 100, 600, 396);
		getContentPane().setLayout(new BorderLayout());
		contentPanel.setBorder(new EmptyBorder(5, 5, 5, 5));
		getContentPane().add(contentPanel, BorderLayout.CENTER);

		JLabel lblTop = new JLabel(Messages.getString("JShowHelpDialog.lblTop.text")); //$NON-NLS-1$

		JScrollPane scrollPane = new JScrollPane();
		GroupLayout gl_contentPanel = new GroupLayout(contentPanel);
		gl_contentPanel.setHorizontalGroup(gl_contentPanel
				.createParallelGroup(Alignment.LEADING).addGroup(gl_contentPanel.createSequentialGroup()
						.addComponent(lblTop).addContainerGap(107, Short.MAX_VALUE))
				.addComponent(scrollPane, GroupLayout.DEFAULT_SIZE, 424, Short.MAX_VALUE));
		gl_contentPanel.setVerticalGroup(gl_contentPanel.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_contentPanel.createSequentialGroup().addComponent(lblTop)
						.addPreferredGap(ComponentPlacement.RELATED).addComponent(scrollPane, GroupLayout.DEFAULT_SIZE,
								198, Short.MAX_VALUE)));

		txtText = new JTextArea();
		txtText.setLineWrap(true);
		txtText.setWrapStyleWord(true);
		txtText.setFont(new Font("Segoe UI", Font.PLAIN, 12));
		txtText.setForeground(Color.BLACK);
		txtText.setEditable(false);
		txtText.setText(Messages.getString("")); //$NON-NLS-1$
		scrollPane.setViewportView(txtText);
		contentPanel.setLayout(gl_contentPanel);
		{
			JPanel buttonPane = new JPanel();
			buttonPane.setLayout(new FlowLayout(FlowLayout.RIGHT));
			getContentPane().add(buttonPane, BorderLayout.SOUTH);
			{
				JButton btnOK = new JButton(Messages.getString("JShowHelpDialog.btnOK.text")); //$NON-NLS-1$
				btnOK.addActionListener(new ActionListener() {
					@Override
					public void actionPerformed(ActionEvent arg0) {
						setVisible(false);
						dispose();
					}
				});
				{
					JButton btnSkip = new JButton(Messages.getString("JShowHelpDialog.btnSkip.text")); //$NON-NLS-1$
					btnSkip.addActionListener(new ActionListener() {
						@Override
						public void actionPerformed(ActionEvent e) {
							if (_configKey != null) {
								// set false to do not show again
								Config.put(_configKey, false);
							}
							setVisible(false);
							dispose();
						}
					});
					btnSkip.setActionCommand(Messages.getGlobalString("btn.cancel"));
					buttonPane.add(btnSkip);
				}
				btnOK.setActionCommand(Messages.getGlobalString("btn.ok"));
				buttonPane.add(btnOK);
				getRootPane().setDefaultButton(btnOK);
			}
		}
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent e) {
				CommonExceptionHandle.IsHasException = false;
			}

			@Override
			public void windowDeactivated(WindowEvent e) {
				CommonExceptionHandle.IsHasException = false;
			}
		});

	}
}
