package main;

import java.awt.BorderLayout;
import java.awt.Toolkit;
import java.util.Locale;

import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.border.EmptyBorder;

import common.Enumeration.EnumConfigKey;
import javafx.application.Platform;
import javafx.beans.value.ChangeListener;
import javafx.beans.value.ObservableValue;
import javafx.embed.swing.JFXPanel;
import javafx.scene.Scene;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;
import mk.constant.Constant;
import mkgethtml.SettingOption;
import resource.text.Messages;

public class PreviewHtml extends JFrame {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private JPanel contentPane;
	private JFXPanel jfxPanel = new JFXPanel();
	private WebEngine engine;
	private String currentTitle = "";

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		SwingUtilities.invokeLater(new Runnable() {

			@Override
			public void run() {
				PreviewHtml preview = new PreviewHtml();
				preview.setVisible(true);
			}
		});
	}

	/**
	 * Create the frame.
	 */
	public PreviewHtml() {
		super();
		init();
	}

	/**
	 * 
	 */
	public void init() {
		createScene();
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		setIconImage(Toolkit.getDefaultToolkit().getImage(PreviewHtml.class.getResource("/resource/box-16.png")));
		setTitle(Messages.getString("PreviewHtml.this.title")); //$NON-NLS-1$
		setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		setBounds(100, 100, 600, 460);
		contentPane = new JPanel();
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));
		contentPane.setLayout(new BorderLayout(0, 0));
		setContentPane(contentPane);
		contentPane.add(jfxPanel, BorderLayout.CENTER);
	}

	private void createScene() {

		Platform.runLater(new Runnable() {
			@Override
			public void run() {
				WebView view = new WebView();
				engine = view.getEngine();
				engine.titleProperty().addListener(new ChangeListener<String>() {
					@Override
					public void changed(ObservableValue<? extends String> observable, String oldValue,
							final String newValue) {
						SwingUtilities.invokeLater(new Runnable() {
							@Override
							public void run() {
								if (currentTitle != newValue) {
									currentTitle = newValue;
									PreviewHtml.this.setTitle(
											Messages.getString("PreviewHtml.this.title") + ": " + currentTitle);
								}
							}
						});
					}
				});

				jfxPanel.setScene(new Scene(view));
			}
		});
	}

	/**
	 * load html content to webview
	 */
	public void loadHtmlContent(final String htmlContent) {
		Platform.runLater(new Runnable() {
			@Override
			public void run() {
				engine.loadContent(htmlContent);
			}
		});
	}

}
