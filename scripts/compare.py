#!/usr/bin/python

"""
Created on April 3, 2018

@author: flg-ma
@attention: compare the output results of the ATF tests
@contact: albus.marcel@gmail.com (Marcel Albus)
@version: 1.0.0


#############################################################################################

History:
- v1.0.0: first push
"""

import yaml
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
from matplotlib.patches import Rectangle
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, DrawingArea, HPacker
from bcolors import TerminalColors as tc
import getpass


class CompareResults:
    def __init__(self, filepath=None):
        print tc.OKBLUE + '=' * 100 + tc.ENDC
        print tc.OKBLUE + '=' * 42 + ' Compare Results ' + '=' * 41 + tc.ENDC
        print tc.OKBLUE + '=' * 100 + tc.ENDC
        try:
            if filepath is None:
                self.pth = raw_input(
                    'Please enter Path to generated testcase output (e.g: \'/home/' + getpass.getuser() + '/Test/\'): ')
            else:
                self.pth = filepath
            if os.path.exists(self.pth + 'Dataframe.csv'):
                pass
            else:
                print 'Collecting directories in given path...'
                self.directories = os.walk(self.pth).next()[1]
        except StopIteration:  # catch error when there is no valid directory given
            exit('The directory path does not exist')

        print '=' * 100

        self.yaml_directory = 'results_yaml'  # output 'yaml'-directory
        self.yaml_name = 'ts0_c0_r0_e0_0.yaml'  # output 'yaml'-name
        # testcases for ATF
        self.testcases = ['line_passage',  # 0
                          'line_passage_obstacle',  # 1
                          'line_passage_person_moving',  # 2
                          'line_passage_spawn_obstacle',  # 3
                          'narrow_passage_2_cone',  # 4
                          't_passage',  # 5
                          't_passage_obstacle']  # 6
        # metrics for ATF
        self.metrics = ['path_length',
                        'goal',
                        'jerk',
                        'time']


    def read_yaml(self):
        '''
        reads the output yaml-files of the ATF and saves them as a pandas dataframe
        :return: pandas dataframe with all metrics values
        '''
        if os.path.exists(self.pth + 'Dataframe.csv'):
            df = pd.read_csv(self.pth + 'Dataframe.csv')
        else:
            data_dict = {}
            columns = ['testcase', 'test_number']  # columns of the pandas dataframe...
            columns.extend(self.metrics)  # ... extended with the metrics
            df = pd.DataFrame([], columns=columns)  # setup dataframe with the testcases as columns
            for items in self.testcases:
                data_dict[items] = {}  # create a dict inside a dict for all testcases
            counter = 0
            for folder in self.directories:
                try:  # if the dataname includes no number...
                    except_flag = False
                    testcase_number = int(filter(str.isdigit, folder))  # number of testcase is saved
                except ValueError as e:
                    except_flag = True
                    print 'No number in testcase found, assuming only one test was made...'
                if ('narrow' in folder) and (not except_flag) and (testcase_number != 2):
                    # save testcase name from folder name without number
                    testcase_name = folder[: -(len(str(testcase_number)))]
                    # narrow_passage_2_cone would save the '2' from the name as number --> not needed
                    testcase_number = int(str(testcase_number)[1:])
                elif not except_flag and not ('narrow' in folder):
                    # save testcase name from folder name without number when it's not 'narrow_passage_2_cone'
                    testcase_name = folder[: -(len(str(testcase_number)) + 1)]
                else:
                    testcase_number = 0  # ... zero is saved as number
                    testcase_name = folder

                filepath = self.pth + folder + '/' + self.yaml_directory + '/' + self.yaml_name
                if os.path.exists(filepath):  # save the data from the 'yaml' if there is an output file
                    stream = file(filepath, 'r')  # open filestream for yaml
                    data_dict[testcase_name][testcase_number] = yaml.load(stream)  # save yaml in dict

                    # create a data dict to append at the dataframe
                    data = {'testcase': testcase_name,
                            'test_number': testcase_number,
                            'path_length': data_dict[testcase_name][testcase_number]['testblock_nav']['path_length'][0][
                                'data'],
                            'goal': data_dict[testcase_name][testcase_number]['testblock_nav']['goal'][0]['data'],
                            'jerk': data_dict[testcase_name][testcase_number]['testblock_nav']['jerk'][0]['data'],
                            'time': data_dict[testcase_name][testcase_number]['testblock_nav']['time'][0]['data']}
                    df = df.append(data, ignore_index=True)  # append data to dataframe
                    stream.close()  # close filestream
                else:  # if there is no generated output 'yaml'-file, save only the testcase name and number
                    data = {'testcase': testcase_name,
                            'test_number': testcase_number,
                            'path_length': np.nan,  # set values to 'np.nan'
                            'goal': np.nan,
                            'jerk': np.nan,
                            'time': np.nan}
                    df = df.append(data, ignore_index=True)  # append data to dataframe
                    data_dict[testcase_name][testcase_number] = None
                # increase counter
                counter += 1
                #
                if counter % 20 == 0:
                    print 'Directories saved: ' + str(counter) + ' / ' + str(self.directories.__len__())

        self.dataframe = df.copy()  # save dataframe globally
        self.dataframe.to_csv(self.pth + 'Dataframe.csv', index=False)
        print 'save \'dataframe\' as \'csv\''
        print '=' * 100
        # df = df.pivot(index='testcase', columns='test_number', values='bool')  # create the desired table output

        formatted_testcases = ['Line Passage',
                               'Line Passage Obstacle',
                               'Line Passage Person Moving',
                               'Line Passage Spawn Obstacle',
                               'Narrow Passage Two Cone',
                               'T Passage',
                               'T Passage Obstacle']

        # i = 0
        # for cases in self.testcases:  # rename the row indices to nice, formatted names
        #     df = df.rename(index={cases: formatted_testcases[i]})
        #     i += 1
        print df.head(10)  # print the first 'n' numbers of the table
        print '=' * 100
        return df  # returns the dataframe

    def plot_heatmap(self, dataframe_list):
        '''
        creates a seaborn heatmap with the provided dataframe
        :param dataframe_list: a list with pandas dataframe including the heatmap data
        :return: -
        '''
        # fig = plt.figure(1, figsize=(self.directories.__len__() / 20.0, self.directories.__len__() / 90.0)) # stupid
        # fig = plt.figure(1, figsize=(dataframe.columns.__len__() / 3.0, dataframe.columns.__len__() / 7.0)) # more line output

        for n in xrange(1, dataframe_list.__len__()):
            x_width = (dataframe_list[n].columns.__len__() / 3.0) if (dataframe_list[
                                                                          n].columns.__len__() / 3.0) > 7.0 else 7.0
            y_height = (dataframe_list[n].columns.__len__() / 7.0) if (dataframe_list[
                                                                           n].columns.__len__() / 7.0) > 3.0 else 3.0
            fig = plt.figure(n, figsize=(x_width, y_height))
            # fig = plt.figure(1, figsize=(7.0, 3.0)) # one line output
            # fig = plt.figure(1, figsize=(200.0, 50.0))

            # setup seaborn for grey output as np.NaN values and no lines indicating the row and columns
            sns.set()  # setup seaborn

            # create heatmap
            ax = sns.heatmap(dataframe_list[n], linewidths=.3, cbar=False,
                             cmap=mpl.colors.ListedColormap(['red', 'yellow', 'green']), square=True, annot=False,
                             vmax=1.0,
                             vmin=0.0)
            plt.xticks(rotation=90)
            # bugfix for the 'bbox_inches=tight' layout, otherwise the label will be cut away
            plt.title('$\quad$', fontsize=60)
            # plt.title('$\quad$', fontsize=35)
            plt.xlabel('Testcase number', fontsize=15)
            plt.ylabel('Testcase', fontsize=15)
            self.plot_rectangle(figure=fig, axis=ax)
            plt.savefig(self.pth + 'Heatmap_Threshold_' + str(n) + '.pdf', bbox_inches='tight')
            fig.clf()
            sns.reset_orig()
            # plt.show()  # show heatmap

    def drop_threshold(self, dataframe_bool):
        '''
        drops the columns when the number of 'True'-bool parameters (given as float) are below the threshold
        the dataframe contains only the bool values (stored as float)
        :param dataframe_bool: dataframe to drop column
        :return: dataframe list with all the dataframes including less columns
        '''
        dataframe_list = []
        for threshold in xrange(0, 8):
            df = pd.DataFrame.copy(dataframe_bool)
            counter = 0
            # bool values in dataframe are stored as float
            for column in df:  # go through each column
                for value in df[column]:  # get values in each column
                    counter += value  # add all values
                if counter < threshold:  # compare with threshold
                    df = df.drop([column], axis=1)  # drop if below threshold
                counter = 0  # reset counter
            dataframe_list.append(df)
        return dataframe_list

    def plot_rectangle(self, figure, axis):
        '''
        plots the legend rectangle above the left corner of the figure
        :param figure: figure on which to add the label
        :param axis: axis on which to add the label
        :return: -
        '''

        box1 = TextArea(" True: \n False: \n NaN: ", textprops=dict(color="k", size=10))

        # box2 = DrawingArea(20, 27.5, 0, 0)
        # el1 = Rectangle((5, 15), width=10, height=10, angle=0, fc="g")
        # el2 = Rectangle((5, 2.5), width=10, height=10, angle=0, fc="r")
        box2 = DrawingArea(20, 45, 0, 0)
        el1 = Rectangle((5, 30), width=10, height=10, angle=0, fc="g")
        el2 = Rectangle((5, 18.5), width=10, height=10, angle=0, fc="r")
        el3 = Rectangle((5, 7), width=10, height=10, angle=0, fc='#d3d3d3')
        box2.add_artist(el1)
        box2.add_artist(el2)
        box2.add_artist(el3)

        box = HPacker(children=[box1, box2],
                      align="center",
                      pad=0, sep=5)

        anchored_box = AnchoredOffsetbox(loc=3,
                                         child=box, pad=0.,
                                         frameon=True,
                                         bbox_to_anchor=(0., 1.02),
                                         bbox_transform=axis.transAxes,
                                         borderpad=0.,
                                         )

        axis.add_artist(anchored_box)
        figure.subplots_adjust(top=0.8)

    def plot_error_bar(self):

        df = self.dataframe.copy()
        df = df.drop(['test_number'], axis=1)
        print df.head(5)  # print first 'n' rows
        print '=' * 100
        gp = df.groupby(['testcase'])

        rename_dict = {'line_passage': 'Line Passage',
                       'line_passage_obstacle': 'Line Passage\nObstacle',
                       'line_passage_person_moving': 'Line Passage\nPerson Moving',
                       'line_passage_spawn_obstacle': 'Line Passage\nSpawn Obstacle',
                       'narrow_passage_2_cone': 'Narrow Passage\nTwo Cone',
                       't_passage': 'T Passage',
                       't_passage_obstacle': 'T Passage\nObstacle'}
        means = gp.mean().rename(index=rename_dict)  # first mean, then rename, otherwise no errorbars are shown
        error = gp.std().rename(index=rename_dict)  # rename standard deviation
        print tc.OKBLUE + 'average values' + tc.ENDC
        print means
        print '=' * 100
        print tc.OKBLUE + 'standard deviation' + tc.ENDC
        print error

        scale_factor = 1.2
        fig = plt.figure(222, figsize=(13.8 * scale_factor, 12.6 * 2.2))
        ax1 = fig.add_subplot(411)
        ax = means.plot.bar(yerr=error, ax=ax1, error_kw={'elinewidth': 2})
        plt.xticks(rotation=90, fontsize=20)
        ax.xaxis.label.set_size(20)
        plt.legend(loc=2, fontsize=12)
        plt.grid(True)
        plt.savefig(self.pth + 'Errorbar.pdf', bbox_inches='tight')
        fig.clf()
        # plt.show()

    def main(self):
        self.read_yaml()
        # self.plot_heatmap(self.drop_threshold(dataframe_bool=self.read_yaml()))
        self.plot_error_bar()
        # print tc.OKGREEN + '=' * 41 + ' Created Heatmap ' + '=' * 41 + tc.ENDC


if __name__ == '__main__':
    cr = CompareResults()
    cr.main()
