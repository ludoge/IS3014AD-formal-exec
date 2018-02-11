from tests.tests import *
from formal_exec.formal_executor import *
import importlib

if __name__ == '__main__':
    chosen_prog = input("Choose program name to use in the data directory.\nIf no name is given or the name given is invalid, default_prog will be loaded.\n> ")
    try:
        module = importlib.import_module("data." + chosen_prog)
        prog = getattr(module, 'prog')
        test = getattr(module, 'test')
    except ModuleNotFoundError:
        module = importlib.import_module("data.default_prog")
        prog = getattr(module, 'prog')
        test = getattr(module, 'test')
    print(prog)
    print()
    chosen_test = None
    while chosen_test not in ['1', '2']:
        chosen_test = input("Press 1 for running test.\nPress 2 for test generation.\n> ")
    k_list = [int(input("Choose k for k-path.\n> "))]
    i_list = [int(input("Choose i for i-loop.\n> "))]
    if chosen_test == '1':
        print("Test TA")
        testTA = TestTA(copy.deepcopy(test))
        print(f"Coverage of {int(testTA.runTests(copy.deepcopy(prog))*100)/100}%")
        print("Test TD")
        testTD = TestTD(copy.deepcopy(test))
        print(f"Coverage of {int(testTD.runTests(copy.deepcopy(prog))*100)/100}%")
        print(f"Test {k_list[0]}-TC")
        testkTC = TestkTC(copy.deepcopy(test), k_list[0])
        print(f"Coverage of {int(testkTC.runTests(copy.deepcopy(prog))*100)/100}%")
        print(f"Test {i_list[0]}-TB")
        testiTB = TestiTB(copy.deepcopy(test), i_list[0])
        print(f"Coverage of {int(testiTB.runTests(copy.deepcopy(prog))*100)/100}%")
        print("Test TDef")
        testTDef = TestTDef(copy.deepcopy(test))
        print(f"Coverage of {int(testTDef.runTests(copy.deepcopy(prog))*100)/100}%")
        print("Test TU")
        testTU = TestTU(copy.deepcopy(test))
        print(f"Coverage of {int(testTU.runTests(copy.deepcopy(prog))*100)/100}%")
        print("Test DU")
        testDU = TestDU(copy.deepcopy(test))
        print(f"Coverage of {int(testDU.runTests(copy.deepcopy(prog))*100)/100}%")
        print("Test TC")
        testTC = TestTC(copy.deepcopy(test))
        print(f"Coverage of {int(testTC.runTests(copy.deepcopy(prog))*100)/100}%")
    elif chosen_test == '2':
        generated_test = FullTest(prog, k_list, i_list).findFullTest()
        print(generated_test)
