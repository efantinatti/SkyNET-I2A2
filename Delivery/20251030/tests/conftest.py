import sys
import types

# Dummy pandas
pandas = types.ModuleType('pandas')
# Provide a dummy spec so importlib can find it
import importlib.machinery
pandas.__spec__ = importlib.machinery.ModuleSpec(name='pandas', loader=None)

# Dummy Series class for type hints used in eda_analyzer
class Series(list):
    """Simple list subclass to mimic pandas.Series behavior needed in tests."""
    def __init__(self, data=None):
        super().__init__(data or [])
    # Provide basic methods used in code (e.g., .mean, .std) as placeholders
    def mean(self):
        return 0
    def std(self):
        return 0
    def median(self):
        return 0
    def quantile(self, q):
        return 0
    def __getitem__(self, idx):
        return super().__getitem__(idx)


class DummyDataFrame:
    def __init__(self, data, columns=None):
        self._data = data
        self.columns = columns or []
    def select_dtypes(self, include=None):
        # Return self with empty numeric columns for simplicity
        return self
    @property
    def columns(self):
        return []
    def __getitem__(self, key):
        return []
    def count(self):
        return 0
    def mean(self):
        return 0
    def median(self):
        return 0
    def std(self):
        return 0

pandas.DataFrame = DummyDataFrame
pandas.Series = Series
sys.modules['pandas'] = pandas

# Dummy pdf2image
pdf2image = types.ModuleType('pdf2image')

def dummy_convert_from_path(pdf_path, dpi=300):
    return []

pdf2image.convert_from_path = dummy_convert_from_path

def dummy_convert_from_bytes(pdf_bytes, dpi=300):
    return []

pdf2image.convert_from_bytes = dummy_convert_from_bytes

# Dummy pypdf module
pypdf = types.ModuleType('pypdf')
class DummyPage:
    def __init__(self, text=''):
        self._text = text
    def extract_text(self):
        return self._text
class PdfReader:
    def __init__(self, path):
        self.pages = []
    # No further methods needed
pypdf.PdfReader = PdfReader
sys.modules['pypdf'] = pypdf
sys.modules['pdf2image'] = pdf2image

# Dummy pdf2image.exceptions
pdf2image_ex = types.ModuleType('pdf2image.exceptions')
class PDFInfoNotInstalledError(Exception):
    pass
pdf2image_ex.PDFInfoNotInstalledError = PDFInfoNotInstalledError
sys.modules['pdf2image.exceptions'] = pdf2image_ex

# Dummy pytesseract
pytesseract = types.ModuleType('pytesseract')
# Provide nested attribute structure expected by code
pytesseract.pytesseract = types.SimpleNamespace(tesseract_cmd='tesseract')
class TesseractNotFoundError(Exception):
    pass
pytesseract.TesseractNotFoundError = TesseractNotFoundError

def dummy_image_to_string(image, lang='por', config=''):
    return ''

def dummy_get_tesseract_version():
    return 'dummy'

pytesseract.image_to_string = dummy_image_to_string
pytesseract.get_tesseract_version = dummy_get_tesseract_version
sys.modules['pytesseract'] = pytesseract

# Dummy streamlit
streamlit = types.ModuleType('streamlit')
streamlit.secrets = {}  # dict provides .get method


class _DummySessionState(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class _DummySpinner:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


streamlit.session_state = _DummySessionState()

def _no_op(*args, **kwargs):
    return None

streamlit.error = _no_op
streamlit.warning = _no_op
streamlit.info = _no_op
streamlit.success = _no_op
streamlit.write = _no_op
streamlit.spinner = lambda *args, **kwargs: _DummySpinner()

sys.modules['streamlit'] = streamlit

# Dummy langchain_google_genai
lg = types.ModuleType('langchain_google_genai')
class ChatGoogleGenerativeAI:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return None
lg.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
sys.modules['langchain_google_genai'] = lg

# Dummy pydantic
pydantic = types.ModuleType('pydantic')
class BaseModel:
    def __init__(self, **data):
        # Store provided fields as attributes
        for key, value in data.items():
            setattr(self, key, value)
    def dict(self, *args, **kwargs):
        # Return a dict of the instance's __dict__
        return {k: v for k, v in self.__dict__.items()}
    def json(self, *args, **kwargs):
        import json as _json
        return _json.dumps(self.dict())

def Field(*args, **kwargs):
    return None
pydantic.BaseModel = BaseModel
pydantic.Field = Field
sys.modules['pydantic'] = pydantic

# Dummy PIL module with proper attributes
pil = types.ModuleType('PIL')

# Submodule PIL.Image
image_mod = types.ModuleType('PIL.Image')

# Dummy Image class used for type hints and runtime
class Image:
    def __init__(self, *args, **kwargs):
        pass
    @staticmethod
    def open(path):
        return Image()
    # Minimal methods used in code
    def convert(self, mode):
        return self
    @property
    def mode(self):
        return 'L'
    @property
    def size(self):
        return (1000, 1000)
    def resize(self, size, resample=None):
        return self

# Attach class to submodule
image_mod.Image = Image

# Exception class
class UnidentifiedImageError(Exception):
    pass
image_mod.UnidentifiedImageError = UnidentifiedImageError

# Add Resampling enum with LANCZOS attribute
class DummyResampling:
    LANCZOS = 'LANCZOS'
image_mod.Resampling = DummyResampling

# Add ImageEnhance submodule with Contrast class
image_enhance_mod = types.ModuleType('PIL.ImageEnhance')
class DummyContrast:
    def __init__(self, image):
        self.image = image
    def enhance(self, factor):
        return self.image
image_enhance_mod.Contrast = DummyContrast
sys.modules['PIL.ImageEnhance'] = image_enhance_mod

# Expose submodule as attribute of top-level PIL module
pil.Image = image_mod
pil.UnidentifiedImageError = UnidentifiedImageError
pil.ImageEnhance = image_enhance_mod

# Register modules
sys.modules['PIL'] = pil
sys.modules['PIL.Image'] = image_mod

# Dummy langchain_google_genai module
lg = types.ModuleType('langchain_google_genai')
class ChatGoogleGenerativeAI:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return None
lg.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
sys.modules['langchain_google_genai'] = lg

# Dummy langchain_core.prompts
lcp = types.ModuleType('langchain_core.prompts')
class ChatPromptTemplate:
    def __init__(self, template: str = ""):
        self.template = template
    @classmethod
    def from_template(cls, template: str):
        return cls(template)
    def format(self, **kwargs):
        return self.template.format(**kwargs)
lcp.ChatPromptTemplate = ChatPromptTemplate
sys.modules['langchain_core.prompts'] = lcp

# Dummy plotly module
plotly = types.ModuleType('plotly')
plotly_express = types.ModuleType('plotly.express')

def dummy_scatter(*args, **kwargs):
    class DummyFigure:
        def show(self):
            pass
        def to_json(self):
            return '{}'
    return DummyFigure()

plotly_express.scatter = dummy_scatter
plotly.express = plotly_express
sys.modules['plotly'] = plotly
sys.modules['plotly.express'] = plotly_express

# Dummy langchain_core.output_parsers
lco = types.ModuleType('langchain_core.output_parsers')
class JsonOutputParser:
    def __init__(self, pydantic_object=None):
        self.pydantic_object = pydantic_object
    def parse(self, text: str):
        # Very naive JSON parsing fallback
        import json
        try:
            return json.loads(text)
        except Exception:
            return {}
lco.JsonOutputParser = JsonOutputParser
sys.modules['langchain_core.output_parsers'] = lco

# Dummy google.generativeai module
google_mod = types.ModuleType('google')
genai_mod = types.ModuleType('google.generativeai')
def dummy_configure(api_key=None):
    return None
class DummyGenerativeModel:
    def __init__(self, *args, **kwargs):
        pass
    def generate_content(self, *args, **kwargs):
        class Resp:
            text = ''
        return Resp()
genai_mod.configure = dummy_configure
genai_mod.GenerativeModel = DummyGenerativeModel
google_mod.generativeai = genai_mod
sys.modules['google'] = google_mod
sys.modules['google.generativeai'] = genai_mod

# Dummy langchain_core.messages (existing)
# Dummy langchain_core.messages
lcm = types.ModuleType('langchain_core.messages')
class HumanMessage:
    def __init__(self, content):
        self.content = content
class SystemMessage:
    def __init__(self, content):
        self.content = content
lcm.HumanMessage = HumanMessage
lcm.SystemMessage = SystemMessage
sys.modules['langchain_core.messages'] = lcm

lcm = types.ModuleType('langchain_core.messages')
class HumanMessage:
    def __init__(self, content):
        self.content = content
class SystemMessage:
    def __init__(self, content):
        self.content = content
lcm.HumanMessage = HumanMessage
lcm.SystemMessage = SystemMessage
sys.modules['langchain_core.messages'] = lcm
