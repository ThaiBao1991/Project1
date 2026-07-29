package main;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Toolkit;
import java.awt.datatransfer.StringSelection;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
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
import mkgethtml.SettingOption;
import resource.text.Messages;

import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

public class JExceptionDialog extends JDialog {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		try {
			JExceptionDialog dialog = new JExceptionDialog();
			dialog.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
			dialog.setVisible(true);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	private final JPanel contentPanel = new JPanel();
	String error = "";
	JTextArea txtText;

	private JTextArea txtText_1;

	public JExceptionDialog() {

		setType(Type.POPUP);
		setAlwaysOnTop(true);

		init();
	}

	/**
	 * Create the dialog.
	 */

	public JExceptionDialog(String err) {
		this.error = err;
		init();
	}

	private void init() {
		setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
			Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
		}
		setIconImage(Toolkit.getDefaultToolkit().getImage(JExceptionDialog.class.getResource("/resource/box-32.png")));
		setTitle(Messages.getString("JExceptionDialog.this.title")); //$NON-NLS-1$
		setBounds(100, 100, 600, 396);
		getContentPane().setLayout(new BorderLayout());
		contentPanel.setBorder(new EmptyBorder(5, 5, 5, 5));
		getContentPane().add(contentPanel, BorderLayout.CENTER);

		JLabel lblTop = new JLabel(Messages.getString("JExceptionDialog.lblTop.text")); //$NON-NLS-1$

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

		txtText_1 = new JTextArea();
		txtText_1.setFont(new Font("Segoe UI", Font.PLAIN, 12));
		txtText_1.setForeground(Color.RED);
		txtText_1.setEditable(false);
		txtText_1.setText(Messages.getString("JExceptionDialog.errorText")
				+ "\n-----------------------------------------------\n\n" + error);
		scrollPane.setViewportView(txtText_1);
		contentPanel.setLayout(gl_contentPanel);
		{
			JPanel buttonPane = new JPanel();
			buttonPane.setLayout(new FlowLayout(FlowLayout.RIGHT));
			getContentPane().add(buttonPane, BorderLayout.SOUTH);
			{
				JButton btnOK = new JButton(Messages.getString("JExceptionDialog.btnCopyAndPost.txt"));
				btnOK.addActionListener(new ActionListener() {
					@Override
					public void actionPerformed(ActionEvent arg0) {
						java.awt.Toolkit.getDefaultToolkit().getSystemClipboard()
								.setContents(new StringSelection("[COLOR=\"#FF0000\"]" + error + "[/COLOR]"), null);
						try {
							java.awt.Desktop.getDesktop()
									.browse(new URI("http://forum.truyencv.com/newreply.php?p=29792&noquote=1"));
						} catch (IOException | URISyntaxException e) {
							e.printStackTrace();
						}
						setVisible(false);
						dispose();
					}
				});
				btnOK.setActionCommand(Messages.getGlobalString("btn.ok"));
				buttonPane.add(btnOK);
				getRootPane().setDefaultButton(btnOK);
			}
			{
				JButton btnSkip = new JButton(Messages.getGlobalString("btn.skip"));
				btnSkip.addActionListener(new ActionListener() {
					@Override
					public void actionPerformed(ActionEvent e) {
						setVisible(false);
						dispose();
					}
				});
				btnSkip.setActionCommand(Messages.getGlobalString("btn.cancel"));
				buttonPane.add(btnSkip);
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
