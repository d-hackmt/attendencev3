import sys

def get_version(pkg):
    try:
        module = __import__(pkg)
        return module.__version__
    except Exception:
        return "Not Installed"

packages = [
"streamlit" ,
"pandas" ,
"python-dotenv ", 
"pytz" ,
"supabase" ,
"requests" ,
"PyGithub" ,
"matplotlib" ,
"typing_extensions",
"ipykernel",
"langchain"                     ,              
"langchain-core"                ,
"langchain-community"          ,
"langchain-text-splitters"     ,
"streamlit"                     ,
"python-dotenv"                 ,
"setuptools"                    
"langchain_google_genai" ,
"langchain-groq"  ,
"langchain-tavily" 
]

print("\n📦 Installed Package Versions\n")
for pkg in packages:
    print(f"{pkg}: {get_version(pkg)}")

print("\nPython Version:", sys.version)
