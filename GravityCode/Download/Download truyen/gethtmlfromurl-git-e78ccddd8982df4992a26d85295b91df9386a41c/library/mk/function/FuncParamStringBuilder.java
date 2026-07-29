package mk.function;

/**
 * inject funtion and return StringBuilder
 * @author nxcuo
 *
 */
public interface FuncParamStringBuilder {
	/**
	 * do something with StringBuilder
	 * @param sb
	 * @return
	 */
	StringBuilder call(StringBuilder sb);
}
