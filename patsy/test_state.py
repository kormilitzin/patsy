from patsy.state import *

def stateful_test(cls, input, output, *args, **kwargs):
    input = np.asarray(input)
    output = np.asarray(output)
    test_cases = [
        # List input, one chunk
        ([input], output),
        # Scalar input, many chunks
        (input, output),
        # List input, many chunks:
        ([[n] for n in input], output),
        # 0-d array input, many chunks:
        ([np.array(n) for n in input], output),
        # 1-d array input, one chunk:
        ([np.array(input)], output),
        # 1-d array input, many chunks:
        ([np.array([n]) for n in input], output),
        # 2-d array input, one chunk:
        ([np.column_stack((input, input[::-1]))],
         np.column_stack((output, output[::-1]))),
        # 2-d array input, many chunks:
        ([np.array([[input[i], input[-i-1]]]) for i in xrange(len(input))],
         np.column_stack((output, output[::-1]))),
        ]
    from patsy.util import have_pandas
    if have_pandas:
        import pandas
        pandas_type = (pandas.Series, pandas.DataFrame)
        pandas_index = np.linspace(0, 1, num=len(input))
        output_series = pandas.Series(output, index=pandas_index)
        input_2d = np.column_stack((input, input[::-1]))
        output_2d = np.column_stack((output, output[::-1]))
        output_dataframe = pandas.DataFrame(output_2d, index=pandas_index)
        test_cases += [
            # Series input, one chunk
            ([pandas.Series(input, index=pandas_index)], output_series),
            # Series input, many chunks
            ([pandas.Series([x], index=[idx])
              for (x, idx) in zip(input, pandas_index)],
             output_series),
            # DataFrame input, one chunk
            ([pandas.DataFrame(input_2d, index=pandas_index)], output_dataframe),
            # DataFrame input, many chunks
            ([pandas.DataFrame([input_2d[i, :]], index=[pandas_index[i]])
              for i in xrange(len(input))],
             output_dataframe),
            ]
    for input_obj, output_obj in test_cases:
        print input_obj
        t = cls()
        for input_chunk in input_obj:
            t.memorize_chunk(input_chunk, *args, **kwargs)
        t.memorize_finish()
        all_outputs = []
        for input_chunk in input_obj:
            output_chunk = t.transform(input_chunk, *args, **kwargs)
            assert output_chunk.ndim == np.asarray(input_chunk).ndim
            all_outputs.append(output_chunk)
        if have_pandas and isinstance(all_outputs[0], pandas_type):
            all_output1 = pandas.concat(all_outputs)
            assert np.array_equal(all_output1.index, pandas_index)
        elif all_outputs[0].ndim == 0:
            all_output1 = np.array(all_outputs)
        elif all_outputs[0].ndim == 1:
            all_output1 = np.concatenate(all_outputs)
        else:
            all_output1 = np.row_stack(all_outputs)
        assert all_output1.shape[0] == len(input)
        # output_obj_reshaped = np.asarray(output_obj).reshape(all_output1.shape)
        # assert np.allclose(all_output1, output_obj_reshaped)
        assert np.allclose(all_output1, output_obj)
        if np.asarray(input_obj[0]).ndim == 0:
            all_input = np.array(input_obj)
        elif have_pandas and isinstance(input_obj[0], pandas_type):
            # handles both Series and DataFrames
            all_input = pandas.concat(input_obj)
        elif np.asarray(input_obj[0]).ndim == 1:
            # Don't use row_stack, because that would turn this into a 1xn
            # matrix:
            all_input = np.concatenate(input_obj)
        else:
            all_input = np.row_stack(input_obj)
        all_output2 = t.transform(all_input, *args, **kwargs)
        if have_pandas and isinstance(input_obj[0], pandas_type):
            assert np.array_equal(all_output2.index, pandas_index)
        assert all_output2.ndim == all_input.ndim
        assert np.allclose(all_output2, output_obj)

def test_Center():
    stateful_test(Center, [1, 2, 3], [-1, 0, 1])
    stateful_test(Center, [1, 2, 1, 2], [-0.5, 0.5, -0.5, 0.5])
    stateful_test(Center,
                  [1.3, -10.1, 7.0, 12.0],
                  [-1.25, -12.65, 4.45, 9.45])

def test_stateful_transform_wrapper():
    assert np.allclose(center([1, 2, 3]), [-1, 0, 1])
    assert np.allclose(center([1, 2, 1, 2]), [-0.5, 0.5, -0.5, 0.5])
    assert center([1.0, 2.0, 3.0]).dtype == np.dtype(float)
    assert (center(np.array([1.0, 2.0, 3.0], dtype=np.float32)).dtype
            == np.dtype(np.float32))
    assert center([1, 2, 3]).dtype == np.dtype(float)

    from patsy.util import have_pandas
    if have_pandas:
        import pandas
        s = pandas.Series([1, 2, 3], index=["a", "b", "c"])
        df = pandas.DataFrame([[1, 2], [2, 4], [3, 6]],
                              columns=["x1", "x2"],
                              index=[10, 20, 30])
        s_c = center(s)
        assert isinstance(s_c, pandas.Series)
        assert np.array_equal(s_c.index, ["a", "b", "c"])
        assert np.allclose(s_c, [-1, 0, 1])
        df_c = center(df)
        assert isinstance(df_c, pandas.DataFrame)
        assert np.array_equal(df_c.index, [10, 20, 30])
        assert np.array_equal(df_c.columns, ["x1", "x2"])
        assert np.allclose(df_c, [[-1, -2], [0, 0], [1, 2]])

def test_Standardize():
    stateful_test(Standardize, [1, -1], [1, -1])
    stateful_test(Standardize, [12, 10], [1, -1])
    stateful_test(Standardize,
                  [12, 11, 10],
                  [np.sqrt(3./2), 0, -np.sqrt(3./2)])

    stateful_test(Standardize,
                  [12.0, 11.0, 10.0],
                  [np.sqrt(3./2), 0, -np.sqrt(3./2)])

    # XX: see the comment in Standardize.transform about why this doesn't
    # work:
    # stateful_test(Standardize,
    #               [12.0+0j, 11.0+0j, 10.0],
    #               [np.sqrt(3./2)+0j, 0, -np.sqrt(3./2)])

    stateful_test(Standardize, [1, -1], [np.sqrt(2)/2, -np.sqrt(2)/2],
                  ddof=1)

    stateful_test(Standardize,
                  range(20),
                  list((np.arange(20) - 9.5) / 5.7662812973353983),
                  ddof=0)
    stateful_test(Standardize,
                  range(20),
                  list((np.arange(20) - 9.5) / 5.9160797830996161),
                  ddof=1)
    stateful_test(Standardize,
                  range(20),
                  list((np.arange(20) - 9.5)),
                  rescale=False, ddof=1)
    stateful_test(Standardize,
                  range(20),
                  list(np.arange(20) / 5.9160797830996161),
                  center=False, ddof=1)
    stateful_test(Standardize,
                  range(20),
                  range(20),
                  center=False, rescale=False, ddof=1)