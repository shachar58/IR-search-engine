import os

class ConfigClass:
    def __init__(self):
        self.corpusPath = r'C:\Users\Koren Levenbrown\Desktop\koren\university\Search_Engine\PartC\data\testData'
        self.savedFileMainFolder = r'C:\Users\Koren Levenbrown\Desktop\koren\university\Search_Engine\PartC\posting'
        self.saveFilesWithStem = os.path.join(self.savedFileMainFolder, "WithStem")
        self.saveFilesWithoutStem = os.path.join(self.savedFileMainFolder, "WithoutStem")
        self.toStem = False

        self.saveFilesDir = self.saveFilesWithoutStem
        if self.toStem:
            self.saveFilesDir = self.saveFilesWithStem

        print('Project was created successfully..')

    def get__corpusPath(self):
        return self.corpusPath
