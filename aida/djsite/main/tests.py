"""
This file contains tests for AIDA.
They are executed when when you run "manage.py test" or
"manage.py test main" (much faster)

"""
from django.utils import unittest
import aida
from aida.djsite.main.models import CalcStatus, CalcType, Code, CodeStatus
from aida.djsite.main.models import CodeType, Computer, Project, Calculation
from aida.djsite.main.models import Element, Potential, PotStatus, PotType
from aida.djsite.main.models import PotAttrTxtVal
from django.contrib.auth.models import User as AuthUser
import getpass
from django.db import IntegrityError
from django.core import management
import json
import os, os.path
import aida.djsite.main
from aida.repository.potential import add_pseudo_file
from aida.common.exceptions import ValidationError
from aida.common.classes import structure
from aida.repository.structure import add_structure
from aida.repository.calculation import add_calculation

# Get the absolute path of the testdata folder, related to the aida module
testdata_folder = os.path.join(
    os.path.dirname(os.path.abspath(aida.__file__)),os.path.pardir,'testdata')


class PseudoTest(unittest.TestCase):
    """
    Test for the pseudopotentials 'Potential' table
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up things once for all tests of this class. 
        In particular, defines a type and a status.
        """
        cls.user, was_created = AuthUser.objects.get_or_create(
            username=getpass.getuser())
        cls.status, was_created = PotStatus.objects.get_or_create(
            name='Unknown')
        cls.type, was_created = PotType.objects.get_or_create(name='pz')
    

    def step1(self):
        """
        Tests insertion of a new pseudo.
        """
        self.new_pot = add_pseudo_file(os.path.join(testdata_folder,
                                                    'Si.pbe-rrkj.UPF'),
                                       description="Test pseudo for Si",
                                       element_symbols=['Si'], 
                                       pot_type=self.type,
                                       pot_status=self.status,user=self.user)
        
    def step1b(self):
        """
        Check M2M relationships on the newly-created potential.
        """
        self.assertEqual(self.new_pot.elements.count(),1)
        self.assertEqual(self.new_pot.elements.get().symbol,'Si')

    def step2(self):
        """
        Test insertion of a pseudo which is identical to the previous one (same 
        md5sum) to see if the 'md5sum' attribute is correctly set.
        """
        new_pot2 = add_pseudo_file(os.path.join(testdata_folder,
            'Si.pbe-rrkj_copy.UPF'),
            description="Test pseudo for Si - just a file copy",
            element_symbols=['Si'], pot_type=self.type,
            pot_status=self.status,user=self.user)

        # I don't catch exceptions: md5sum should be set, and only one
        # such attribute should be present
        md5sum1 = PotAttrTxtVal.objects.get(potential=self.new_pot,
                                            attribute__name="md5sum").value
        md5sum2 = PotAttrTxtVal.objects.get(potential=new_pot2,
                                            attribute__name="md5sum").value
        self.assertEqual(md5sum1, md5sum2)

    def step3(self):
        """
        Test insertion of a pseudo which has a different md5sum (I just modified 
        slightly the content) but with a name that maps on the same name, 
        to see if the title-name generator does it work.
        Test also the algorithm itself for bad symbols removal.
        
        Note:
            actually, the name is different, but the + character is not allowed
            and is stripped out; then, the comparison is done, and the code should
            find a name clash and append a different number to the filename.
        """
        new_pot2 = add_pseudo_file(os.path.join(testdata_folder,
             'Si.pbe-rrkj++.UPF'),
             description=("Test pseudo for Si - similar filename, "
                          "different MD5sum"),
             element_symbols=['Si'], pot_type=self.type,
             pot_status=self.status,user=self.user)

        # I don't catch exceptions: md5sum should be set, and only one
        # such attribute should be present
        md5sum1 = PotAttrTxtVal.objects.get(potential=self.new_pot,
                                            attribute__name="md5sum").value
        md5sum2 = PotAttrTxtVal.objects.get(potential=new_pot2,
                                            attribute__name="md5sum").value
        self.assertNotEqual(md5sum1, md5sum2)

    def step4(self):
        """
        Test insertion of a pseudo referring to an element that does not
        exist.
        """
        with self.assertRaises(ValidationError):
            new_pot2 = add_pseudo_file(os.path.join(testdata_folder,
                 'Si.pbe-rrkj.UPF'),
                 description=("Test pseudo for Si - with wrong "
                              "element list"),
                 element_symbols=['inexistent'], pot_type=self.type,
                 pot_status=self.status,user=self.user)

    def the_steps(self):
        for name in sorted(dir(self)):
            if name.startswith("step"):
                yield name, getattr(self, name) 

    def test_steps(self):
        for name, step in self.the_steps():
            try:
                step()
            except Exception as e:
                import traceback
                print traceback.format_exc()
                self.fail("{} failed ({}: {})".format(step.__name__, e.__class__.__name__, e))
                          
class ElementTest(unittest.TestCase):
    """
    Test if elements have been loaded correctly
    """    
    def test_atoms(self):
        """
        Tests chemical symbols and masses of a few atoms (H, C, O, Ba, Ti).
        """
        a = Element.objects.get(Z=1)
        self.assertEqual(a.symbol, "H")

        a = Element.objects.get(Z=6)
        self.assertEqual(a.symbol, "C")

        a = Element.objects.get(Z=8)
        self.assertEqual(a.symbol, "O")

        # Test also the other way round
        a = Element.objects.get(symbol="Ba")
        self.assertEqual(a.Z, 56)

        a = Element.objects.get(symbol="Ti")
        self.assertEqual(a.Z, 22)
                         
    def test_no_zequalszero(self):
        """
        Test that there is no element with Z=0.
        """
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist):
            Element.objects.get(Z=0)
        

class SubmissionTest(unittest.TestCase):
    # List here fixtures to be load
    # for some reasons it doesn't work... for the moment I just load it in
    # setUp, even if possibly redundant
    #fixtures = ['testcalcstatus']

    def test_submission(self):
        """
        Tests that I can submit a calculation.
        """
        testuser = AuthUser.objects.create(username="test")
        # I insert a new calculation
        project = Project.objects.create(name="test",user=testuser)
        computer = Computer.objects.create(hostname="localhost",user=testuser)
        initial_status = CalcStatus.objects.create(name="test_status")
        calc_type = CalcType.objects.create(name="dft.scf")
        code_status = CodeStatus.objects.create(name="development")
        code_type = CodeType.objects.create(name="Quantum Espresso/pw")
        code = Code.objects.create(name="pw.x",computer=computer,
                                   type=code_type,status=code_status,
                                   user=testuser)

        input_data = {
            'CONTROL': {
                'calculation': 'relax',
                'restart_mode': 'from_scratch',
                },
            'SYSTEM': {
                'ibrav': 0,
                'fixed_magnetization': [0.,1.,0.5],
                'nosym': True,
                },
            'ELECTRONS': {
                'mixing_beta': 0.3,
                },
            'K_POINTS': {
                'type': 'automatic',
                'points': [4, 4, 4, 0, 0, 0],
                },
            }

        input_params={}
        input_params['input_data'] = input_data
        
        # internally calls Calculation.objects.create
        # correctly managing the input_data
        self.the_calc = add_calculation(user=testuser,
            computer=computer, code=code, project=project,
            status=initial_status, type=calc_type, input_params=input_params)

        # There are still no input Sites attached
        with self.assertRaises(ValidationError):
            self.the_calc.submit()
            
        a = 5.43
        sites = structure.Sites(cell=((a/2.,a/2.,0.),
                                      (a/2.,0.,a/2.),
                                      (0.,a/2.,a/2.)),
                                pbc=(True,True,True))
        sites.appendSite(structure.Site(symbols='Si',
                                                 position=(0.,0.,0.)))
        sites.appendSite(structure.Site(symbols='Si',
                                                 position=(a/2.,a/2.,a/2.)))
       
        struct_django = add_structure(sites,user=testuser,dim=3)
        self.the_calc.instructures.add(struct_django)

        # I want to check that I am able to retrieve the file
        retrieved_sites = struct_django.get_sites()
        
        test_cell = retrieved_sites.cell
        self.assertAlmostEqual(test_cell[0][0],a/2.)
        self.assertAlmostEqual(test_cell[0][2],0.)
        self.assertEqual(retrieved_sites.pbc,(True,True,True))
        self.assertEqual(len(retrieved_sites.sites),2)
        self.assertEqual(retrieved_sites.sites[0].symbols,('Si',))
        self.assertAlmostEqual(retrieved_sites.sites[1].position[0],a/2.)

        self.the_calc.submit()
