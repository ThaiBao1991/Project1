package main;

import java.awt.Color;
import java.awt.Component;
import java.awt.EventQueue;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Locale;

import javax.swing.ButtonGroup;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.WindowConstants;
import javax.swing.border.EmptyBorder;
import javax.swing.border.TitledBorder;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import javax.swing.text.BadLocationException;

import org.eclipse.wb.swing.FocusTraversalOnArray;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.SettingOption;
import resource.text.Messages;

public class FindAndReplace extends JDialog {

	/**
	 * 
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
					FindAndReplace frame = new FindAndReplace();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private JPanel contentPane;
	private JTextField txtSearch;
	private JTextField txtReplace;
	private JLabel lblStatus;
	private JButton btnCacel, btnReplace, btnReplaceAll, btnFind;
	JTextArea text;
	private JPanel panel;
	private JRadioButton rdbtnSearchUp;
	private JRadioButton rdbtnSearchDown;

	private int currentPos = -1;

	/**
	 * Create the frame.
	 */
	public FindAndReplace() {
		setAlwaysOnTop(true);
		setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		init();
	}

	public FindAndReplace(JTextArea text) {
		init();
		this.text = text;
		setAlwaysOnTop(true);
	}

	void findText() {
		if (rdbtnSearchDown.isSelected()) {
			currentPos = text.getText().indexOf(txtSearch.getText(), currentPos + 1);
		} else {
			if (currentPos > -1) {
				try {
					currentPos = text.getText(0, currentPos).lastIndexOf(txtSearch.getText());
				} catch (BadLocationException e) {
					e.printStackTrace();
				}
			} else {
				currentPos = text.getText().lastIndexOf(txtSearch.getText());
			}
		}

		if (currentPos > -1) {
			if (lblStatus.isVisible() && JOptionPane.showConfirmDialog(null,
					(rdbtnSearchDown.isSelected() == true ? Messages.getString("CopyRightInfo.endOfText"): Messages.getString("CopyRightInfo.startOfText"))
							+ Messages.getString("CopyRightInfo.stringNotFound"),
					"Search", JOptionPane.YES_NO_OPTION, JOptionPane.QUESTION_MESSAGE) == JOptionPane.YES_OPTION) {
				lblStatus.setVisible(false);
				currentPos = -1;

			} else {
				lblStatus.setVisible(false);
				text.requestFocus();
				text.setCaretPosition(currentPos);
				text.select(currentPos, currentPos + txtSearch.getText().length());
			}
		} else {

			lblStatus.setVisible(true);
			lblStatus.setText(String.format(Messages.getString("CopyRightInfo.statusNotFound"), txtSearch.getText()));

		}
	}

	void init() {
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
			Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}
		setTitle(Messages.getString("FindAndReplace.this.title")); //$NON-NLS-1$
		setResizable(false);
		setBounds(100, 100, 453, 166);
		contentPane = new JPanel();
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));
		setContentPane(contentPane);

		JLabel lblFindWhat = new JLabel(Messages.getString("FindAndReplace.lblFindWhat.text")); //$NON-NLS-1$

		JLabel lblReplaceWith = new JLabel(Messages.getString("FindAndReplace.lblReplaceWith.text")); //$NON-NLS-1$

		txtSearch = new JTextField();
		txtSearch.setText(Messages.getString("FindAndReplace.txtSearch.text")); //$NON-NLS-1$
		txtSearch.setColumns(10);

		txtReplace = new JTextField();
		txtReplace.setHorizontalAlignment(SwingConstants.LEFT);
		txtReplace.setText(Messages.getString("FindAndReplace.txtReplace.text")); //$NON-NLS-1$
		txtReplace.setColumns(10);

		btnFind = new JButton(Messages.getString("FindAndReplace.btnFind.text")); //$NON-NLS-1$
		btnFind.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				findText();
			}
		});

		btnReplace = new JButton(Messages.getString("FindAndReplace.btnReplace.text")); //$NON-NLS-1$
		btnReplace.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				replaceText();
			}
		});

		btnReplaceAll = new JButton(Messages.getString("FindAndReplace.btnReplaceAll.text")); //$NON-NLS-1$
		btnReplaceAll.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				replaceAllText();
			}
		});

		btnCacel = new JButton(Messages.getString("FindAndReplace.btnCacel.text")); //$NON-NLS-1$
		btnCacel.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				setVisible(false);
				dispose();
			}
		});
		contentPane.setLayout(new FormLayout(
				new ColumnSpec[] { ColumnSpec.decode("2dlu"), ColumnSpec.decode("67px"), ColumnSpec.decode("2dlu"),
						ColumnSpec.decode("224px:grow"), ColumnSpec.decode("2dlu"), ColumnSpec.decode("115px"), },
				new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("top:max(24dlu;min)"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"), }));

		lblStatus = new JLabel(Messages.getString("FindAndReplace.lblStatus.text"));
		lblStatus.setVisible(false);

		panel = new JPanel();
		panel.setBorder(new TitledBorder(null, Messages.getString("FindAndReplace.panel.borderTitle"), TitledBorder.LEFT, TitledBorder.TOP, null, null)); //$NON-NLS-1$
		contentPane.add(panel, "4, 6, left, top");

		rdbtnSearchDown = new JRadioButton(Messages.getString("FindAndReplace.rdbtnSearchDown.text")); //$NON-NLS-1$
		rdbtnSearchDown.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent e) {
				lblStatus.setVisible(false);
			}
		});
		panel.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.UNRELATED_GAP_COLSPEC, ColumnSpec.decode("89px"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("75px"), },
				new RowSpec[] { FormSpecs.MIN_ROWSPEC, }));
		rdbtnSearchDown.setSelected(true);
		panel.add(rdbtnSearchDown, "2, 1, left, top");

		rdbtnSearchUp = new JRadioButton(Messages.getString("FindAndReplace.rdbtnSearchUp.text")); //$NON-NLS-1$
		rdbtnSearchUp.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent e) {
				lblStatus.setVisible(false);
			}
		});
		panel.add(rdbtnSearchUp, "4, 1, left, top");
		ButtonGroup searchChoose = new ButtonGroup();
		searchChoose.add(rdbtnSearchDown);
		searchChoose.add(rdbtnSearchUp);

		lblStatus.setForeground(new Color(220, 20, 60));
		contentPane.add(lblStatus, "2, 8, 3, 1, fill, bottom");
		contentPane.add(btnCacel, "6, 8, fill, top");
		contentPane.add(lblReplaceWith, "2, 4, right, center");
		contentPane.add(lblFindWhat, "2, 2, right, center");
		contentPane.add(txtSearch, "4, 2, fill, center");
		contentPane.add(txtReplace, "4, 4, fill, fill");
		contentPane.add(btnFind, "6, 2, fill, top");
		contentPane.add(btnReplaceAll, "6, 6, fill, top");
		contentPane.add(btnReplace, "6, 4, fill, top");
		contentPane.setFocusTraversalPolicy(new FocusTraversalOnArray(
				new Component[] { txtReplace, txtSearch, btnFind, btnReplace, btnReplaceAll, btnCacel }));
	}

	void replaceAllText() {
		findText();
		if (!lblStatus.isVisible()) {
			text.setText(text.getText().replaceAll(txtSearch.getText(), txtReplace.getText()));
		} else {
			lblStatus.setVisible(true);
			lblStatus.setText(String.format(Messages.getString("CopyRightInfo.statusNotFound"), txtSearch.getText()));
		}
	}

	void replaceText() {
		if (!lblStatus.isVisible() && currentPos > -1) {
			text.replaceSelection(txtReplace.getText());
			btnFind.doClick();
		} else {
			lblStatus.setVisible(true);
			lblStatus.setText(String.format(Messages.getString("CopyRightInfo.statusNotFound"), txtSearch.getText()));
		}
	}
}
