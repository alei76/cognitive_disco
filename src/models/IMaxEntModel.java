package models;

import java.io.IOException;

import org.json.JSONException;
import cc.mallet.classify.ClassifierTrainer;
import cc.mallet.classify.MaxEntTrainer;

public class IMaxEntModel extends IndependentModel {

	public IMaxEntModel(String experimentName, String mappingJson,
			String trainingDir, String devDir, String testDir)
			throws JSONException, IOException {
		super(experimentName, mappingJson, trainingDir, devDir, testDir);
	}
	
	/**
	 * @param args
	 * @throws IOException 
	 * @throws JSONException 
	 */
	public static void main(String[] args) throws JSONException, IOException {
	    
		IndependentModel classifier = new IMaxEntModel(args[0], args[1], 
				"conll15-st-05-19-15-train", "conll15-st-05-19-15-dev", "conll15-st-05-19-15-test");
		classifier.trainTest();
		System.out.println(classifier.dm.toString());
		
	}
	
	public ClassifierTrainer<?> getNewTrainer() {
		return new MaxEntTrainer();
	}

	@Override
	public void classify(String dataDir) {
		// TODO Auto-generated method stub
		
	}
	

}
