# This delcares the main function of the module

# Import the main function from Minerva's cli code
from minerva.cli import main

# If the user is trying to run the __main__ function directly we exit because you're not supposed to do that, :)
if __name__ == "__main__":
    raise SystemExit(main())
